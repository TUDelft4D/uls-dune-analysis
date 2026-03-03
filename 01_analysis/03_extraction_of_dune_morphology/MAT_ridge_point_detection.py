'''
Script and functions to compute the MAT ridge points from a DEM or LAZ file of topography

The MAT implementation in this script is largely based on the masbpy implementation of the shrinking ball algorithm by Peters and Ledoux
see: https://github.com/tudelft3d/masbpy
refer to: 
Peters, Ravi, and Hugo Ledoux. “Robust Approximation of the Medial Axis Transform of LiDAR Point Clouds as a Tool for Visualisation.” Computers & Geosciences 90 (May 2016): 123–33. https://doi.org/10.1016/j.cageo.2016.02.019.
and original introduction by Ma et al., 2012:
Ma, Jaehwan, Sang Won Bae, and Sunghee Choi. “3D Medial Axis Point Approximation Using Nearest Neighbors and the Normal Field.” The Visual Computer 28, no. 1 (2012): 7–19. https://doi.org/10.1007/s00371-011-0594-7.
'''
import numpy as np, laspy, matplotlib.pyplot as plt, rasterio as rio, pandas as pd
from scipy.spatial import KDTree
import argparse
from pathlib import Path
import geopandas as gpd
from shapely.geometry import Point
import os
parser = argparse.ArgumentParser(description="command line interface to extract mat from input tif or las",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('--pc',
                    help=('point cloud or raster in tif format'),
                    default='01_DEMs/20240607_mean.tif',
                    nargs='?',
                    type=str)
parser.add_argument('--output',
                    help=('output folder to write numpy, xyz, and shp file to write medial axes and radius to'),
                    default='05_ridge_lines/ridge_points/',
                    nargs='?',
                    type=str)
parser.add_argument('--nn_normal',
                    help=("number of neighbors for normal vector computation"),
                    default=9,
                    nargs='?',
                    type=int)
parser.add_argument('--r_init',
                    help=("initial radius of shrinking ball in unit of input. Value should depend on the (desired) level of detail and the actual scale of the terrain"),
                    default=10,
                    nargs='?',
                    type=float)
parser.add_argument('--detect_planar',
                    help=("parameter for eliminating planar points. \
                          If angle between the vector  p - ball center and q - ball center is smaller than this parameter a ball is deemed invalid due to the planarity of the surface. \
                          At a perfectly planar surface this angle would be close to 0 degrees."),
                    default=10,
                    nargs='?',
                    type=int)
parser.add_argument('--denoise',
                    help=("Denoising parameter defining the angle (in degrees) between the normal of p, and the vector from the center of the ball (c) to q.\
                          A ball is deemed invalid and we keep the previous if this angle is smaller than _denoise_."),
                    default=8,
                    nargs='?',
                    type=int)
parser.add_argument('--height_amp',
                    help=("height amplification param, if 1 just use normal height"),
                    default=1,
                    nargs='?',
                    type=int)
parser.add_argument('--overwrite',
                    help=("Parameter to enable check if the MAT with the proposed filename already exists, if 0 it doesn't overwrite. Default is 0"),
                    default=0,
                    nargs='?',
                    type=int)
args = parser.parse_args()

def save_pointcloud_shapefile(array, filename, crs, columns=["X", "Y", "Z", "r", "px", "py", "pz", "pi", "qx", "qy", "qz", "qi"]):
    # Define column names matching your XYZ file
    # columns = ["X", "Y", "Z", "r", "px", "py", "pz", "pi", "qx", "qy", "qz", "qi"]
    # Create DataFrame from array
    df = gpd.GeoDataFrame(array, columns=columns)

    # Convert X and Y to Point geometry (Z can be stored as attribute)
    df['geometry'] = [Point(xy) for xy in zip(df["X"], df["Y"])]
    print(crs)
    df.set_crs(crs=crs, inplace=True)

    # Save to shapefile
    df.to_file(filename, driver='ESRI Shapefile')

# compute normals:
def compute_normals(point_cloud, k=9):
    """
    Compute normals for a 3D point cloud using PCA.

    Parameters:
        point_cloud (numpy.ndarray): Nx3 array of 3D points.
        k (int): Number of neighbors to use for normal estimation.

    Returns:
        numpy.ndarray: Nx3 array of normal vectors for each point.
    """
    kd_tree = KDTree(point_cloud)
    normals = []

    for i, point in enumerate(point_cloud):
        # Find the k-nearest neighbors
        distances, indices = kd_tree.query(point, k=k)  #TODO: CHANGE THIS TO RADIUS FOR IRREGULAR POINT CLOUDS!
        neighbors = point_cloud[indices]
        

        # Compute the covariance matrix of the neighbors
        centroid = np.mean(neighbors, axis=0)
        centered_neighbors = neighbors - centroid


        # Compute covariance matrix via SVD
        _, _, vh = np.linalg.svd(centered_neighbors, full_matrices=False)
        normal = vh[2]
        # normalize
        normal /= np.linalg.norm(normal)
        # Garandeer dat de normaal omhoog gericht is.
        if normal[2] < 0:
            normal *= -1
        normals.append(normal)
    
    return np.array(normals)

def cos_angle(p,q):
    """
    From Peters 2016
    Calculate the cosine of angle between vector p and q
    see http://en.wikipedia.org/wiki/Law_of_cosines#Vector_formulation
    """
    cos_angle = np.dot(p,q) / (np.linalg.norm(p) * np.linalg.norm(q) )
    if cos_angle > 1: return 1
    elif cos_angle < -1: return -1
    else: return cos_angle

def compute_medial_ball_center_and_radius(point_cloud, kd_tree, p, i, n, r_init, denoise=None, detect_planar=None):
    """
    Shrinking-ball algorithm to compute the medial ball center and radius.

    Parameters:
        point_cloud (numpy.ndarray): Surface point cloud as a Nx3 array.
        kd_tree (object): kdtree of this point cloud
        p (numpy.ndarray): Surface point (3D coordinates).
        i (int): index of surface point.
        n (numpy.ndarray): Normal vector at point p (3D vector).
        r_init (float): Initial radius of the ball.
        denoise (float): denoising parameter.
        detect_planar (float): planarity parameter

    Returns:
        tuple: Medial ball center (numpy.ndarray) and radius (float).
    """
    if detect_planar != None:
        detect_planar= np.deg2rad(detect_planar)
    if denoise != None:
        denoise = np.deg2rad(denoise)
    q_previous = None
    r_previous = r_init
    count = 0
  
    while True:

        if count > 0:
        # Initialize radius and center
            r_previous = r
            q_previous = q_next
            q_i_previous = q_i_next

        c = p - n * r_previous  # Ball center initialized along the negative normal vector


        # Find the nearest point to c excluding the current point `p`
        distances, indices = kd_tree.query(c, k=2)  # Query 2 nearest points
        if indices[0] == i:
            # if p is closest, we pick the second closest and return:
            q_i_next = indices[1]

            # r = r_init
            # break
        else:
            q_i_next = indices[0]
        q_next = point_cloud[q_i_next]

        # Compute the next radius and center
        d = np.linalg.norm(p - q_next)
        cost = np.dot(n, (p - q_next)) / d
        r = np.abs(d / (2 * cost))

        # from Peters 2016
        if r < 0: 
            r = r_init
        elif r > r_init:
            r = r_init
            break


        c_next = p - n * r  # Update ball center

        if denoise is not None:
            if np.arccos(cos_angle(p-c_next, q_next-c_next)) < denoise and count>0 and r>np.linalg.norm(q_next-p): # maybe leave out count?
                if count < 2:
                    # if just the second loop, the first could be far below denoising level as well if the planar detection would be lower than denoising, thus just dont use
                    r = r_init
                    break
                # keep previous radius:
                r=r_previous
                q_next = q_previous
                q_i_next = q_i_previous
                c_next = c
                break

        if detect_planar != None and count < 1:
            if np.arccos(cos_angle(p-c_next, q_next-c_next)) < detect_planar:
                r = r_init
                break

        # stop iteration if r has converged
        if abs(r_previous - r) < 0.005:
            break

        # stop iteration if this looks like an infinite loop:
        if count > 30:
            break
        count += 1

    if r >= r_init:
        raise ValueError('no valid MAT')

 
    else:
        # check if dist p  c_next, q_next - c_next is equal
        p_c_next = p - c_next
        q_next_c_next = q_next - c_next
        q_next_p = q_next - p
        p_qnext = p - q_next

        
        diff_dist_pc_qc =  np.linalg.norm(p_c_next) - np.linalg.norm(q_next_c_next)
        if diff_dist_pc_qc > 1e-10:
            print(diff_dist_pc_qc)

        # also check if angles are equal
        angles_pq_qc = np.arccos(np.sum(q_next_p * q_next_c_next) / (np.linalg.norm(q_next_p) * np.linalg.norm(q_next_c_next)))
        angles_pq_pc = np.arccos(np.sum(p_qnext * p_c_next) / (np.linalg.norm(p_qnext) * np.linalg.norm(p_c_next)))
        diff_angles = angles_pq_qc - angles_pq_pc
        if diff_angles > 1e-10:
            print(diff_angles)

        return c_next, r, q_next, q_i_next

def projection_point_on_line(line_point1, line_point2, point):
    line_vec = line_point2 - line_point1
    point_vec = point - line_point1
    projection_factor = np.dot(point_vec, line_vec) / np.dot(line_vec, line_vec)
    point_on_line = line_point1 + projection_factor * line_vec
    return point_on_line

def find_ridge_points(point_cloud, p, q, c):
    xy_max = np.max(np.array([p[:2],q[:2]]), axis=0)
    xy_min = np.min(np.array([p[:2],q[:2]]), axis=0)
    point_cloud_subset = point_cloud[(point_cloud[:,0] <= xy_max[0]) & (point_cloud[:,0] >= xy_min[0]) & (point_cloud[:,1] <= xy_max[1]) & (point_cloud[:,1] >= xy_min[1])]
    if len(point_cloud_subset) < 1:
        print('no cells between p and q', p[:2], q[:2])
        return np.nan


    # project the point on the line and find the projected vector
    point_on_line = projection_point_on_line(p, q, c)
    cd = point_on_line - c
    # now find the point where this vector intersects the surface by finding the closest projected point
    dists = []

    # TODO: Do this based on a KDTree instead of this loop?
    for point in point_cloud_subset:
        dist = np.linalg.norm(np.cross(c - point, cd)) / np.linalg.norm(cd)
        dists.append(dist)
    ridge_point = point_cloud_subset[np.argmin(np.array(dists))]
    return ridge_point

if __name__ == '__main__':
    # obtain name of files to write
    vars = [str(value) for value in vars(args).values()][2:]
    name_save = args.output + Path(args.pc).stem + "_" + "_".join(vars) 
    print(args.output, Path(args.pc).stem, name_save)

    if args.denoise == 0:
        args.denoise = None
    if args.detect_planar == 0:
        args.detect_planar = None
    

    if (args.overwrite < 1) and (os.path.exists(name_save[:-1] + "0_ext.shp") or os.path.exists(name_save[:-1] + "0_int.shp") or os.path.exists(name_save[:-1] + "1_ext.shp") or os.path.exists(name_save[:-1] + "1_int.shp")):
        print(f"MAT of point cloud with current settings already exists: {name_save[:-1]}")
    else:
        if Path(args.pc).suffix == '.tif' or Path(args.pc).suffix == '.TIF':
            with rio.open(args.pc) as f_tif:
                zs = f_tif.read(1)
                        # make list of points
                xs, ys = np.meshgrid(np.arange(zs.shape[1]),np.arange(zs.shape[0]))
                
                # do not use nodata points
                crs = f_tif.crs
                transform = f_tif.transform
                # Convert pixel indices (xs, ys) to world coordinates using affine transform
                world_coords = np.array([transform * (x, y) for x, y in zip(xs.flatten(), ys.flatten())])

                # Now stack world_coords and zs
                xyz = np.hstack((world_coords, zs.flatten()[:, np.newaxis]))

                # Remove nodata points
                if  f_tif.nodata < 0:
                    xyz = xyz[xyz[:,2] > (f_tif.nodata + 1)]
                else:
                    xyz = xyz[xyz[:,2] < (f_tif.nodata - 1)]

                # center at mean to keep precision and memory efficiency
                xyz_mean = np.mean(xyz, axis=0)
                print('xyz_mean', xyz_mean)

                xyz -= xyz_mean
                print('xyz_mean', xyz_mean)
                print(crs)

        elif Path(args.pc).suffix == '.las' or Path(args.pc).suffix == '.laz' or Path(args.pc).suffix == '.LAS' or Path(args.pc).suffix == '.LAZ':
            with laspy.open(args.pc) as f_las:
                las = f_las.read()
                xyz = las.xyz
                crs = las.header.parse_crs().to_epsg()
                # center at mean to keep precision and memory efficiency
                xyz_mean = np.mean(xyz, axis=0)
                print(xyz_mean)
                xyz -= xyz_mean
        else:
            raise Exception('unexpected file extension')
        
        # height amplification? Does this do anything? or same influence as denoising parameters?
        # xyz[:,2] *= args.height_amp

        normals = compute_normals(xyz, k=args.nn_normal)
        # Construct KDTree once
        kd_tree = KDTree(xyz)
    
        medial_centers_exterior = []
        medial_centers_interior = []
        
        radii_exterior = []
        radii_interior = []
        
        ps_interior = []
        pis_interior = []
        qs_interior = []
        qis_interior = []

        ps_exterior = []
        pis_exterior = []
        qs_exterior = []
        qis_exterior = []

        for i, (p, n) in enumerate(zip(xyz, normals)):

            if (i % 100) == 0:
                print(f'computing int. + ext. MAT of point {i}/{len(xyz)}')
            r_init = args.r_init  # Initial radius
            try:
                c_in, r_in, q_int, q_i_int = compute_medial_ball_center_and_radius(xyz, kd_tree, p, i, n, r_init, detect_planar=args.detect_planar, denoise=args.denoise)

                medial_centers_interior.append(c_in)
                radii_interior.append(r_in)
                
                ps_interior.append(p)
                pis_interior.append(i)
                qs_interior.append(q_int)
                qis_interior.append(q_i_int)

            except Exception as e:
                pass

            try:
                c_out, r_out, q_ext, q_i_ext  = compute_medial_ball_center_and_radius(xyz, kd_tree, p, i, -1 * n, r_init, detect_planar=args.detect_planar, denoise=args.denoise)
                medial_centers_exterior.append(c_out)
                radii_exterior.append(r_out)

                ps_exterior.append(p)
                pis_exterior.append(i)
                qs_exterior.append(q_ext)
                qis_exterior.append(q_i_ext)
            except Exception as e:
                pass

        medial_centers_exterior = np.array(medial_centers_exterior)
        medial_centers_interior = np.array(medial_centers_interior)

        ps_interior = np.array(ps_interior)
        pis_interior = np.array(pis_interior)
        qs_interior = np.array(qs_interior)
        qis_interior = np.array(qis_interior)

        ps_exterior = np.array(ps_exterior)
        pis_exterior = np.array(pis_exterior)
        qs_exterior = np.array(qs_exterior)
        qis_exterior = np.array(qis_exterior)


        radii_exterior = np.array(radii_exterior)
        radii_interior = np.array(radii_interior)

        # now compute the ridges based on projection of points c on surface (only for internal?)
        # TODO: also for external mat? corridors?
        ridge_points = []
        for i, (p, q, c) in enumerate(zip(ps_interior, qs_interior, medial_centers_interior)):
            if (i % 500) == 0:
                print(f'considering ridge: {i}/{len(medial_centers_interior)}')
            ridge_point = find_ridge_points(xyz, p, q, c)
            ridge_points.append(ridge_point)
        ridge_points = np.array(ridge_points)
        # obtain number of hits per ridge point
        # Use unique with axis=0 and also return_inverse and counts
        unique_rows, inverse, counts = np.unique(ridge_points, axis=0, return_inverse=True, return_counts=True)
        # Map back counts to original array
        count_array = counts[inverse]


        ridge_points += xyz_mean


        # recenter at globe
        print('xyz mean:', xyz_mean)
        print('xyz:', xyz)
        xyz += xyz_mean
        print('xyz:', xyz)
        medial_centers_exterior += xyz_mean
        medial_centers_interior += xyz_mean
        ps_interior += xyz_mean
        qs_interior += xyz_mean
        ps_exterior += xyz_mean
        qs_exterior += xyz_mean

      
        np_ext = np.hstack((medial_centers_exterior, radii_exterior[:, np.newaxis], ps_exterior, pis_exterior[:, np.newaxis],qs_exterior,qis_exterior[:, np.newaxis]))
        np_int = np.hstack((medial_centers_interior, radii_interior[:, np.newaxis], ps_interior, pis_interior[:, np.newaxis],qs_interior,qis_interior[:, np.newaxis]))

        # save shapefile mat + corresponding ridge points
        save_pointcloud_shapefile(np_ext, name_save + "_ext.shp", crs)
        save_pointcloud_shapefile(np_int, name_save + "_int.shp", crs)

        # save all ridge points
        np_int_ridge = np.hstack((ridge_points, radii_interior[:, np.newaxis], ps_interior, pis_interior[:, np.newaxis],qs_interior,qis_interior[:, np.newaxis], count_array[:, np.newaxis]))
        save_pointcloud_shapefile(np_int_ridge, name_save + "_int_ridge.shp", crs, columns=["X", "Y", "Z", "r", "px", "py", "pz", "pi", "qx", "qy", "qz", "qi","count"])





