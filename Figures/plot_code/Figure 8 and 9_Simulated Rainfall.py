import netCDF4
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import shapefile
from scipy.interpolate import griddata
from numpy import nan_to_num
import matplotlib.ticker as mticker
from matplotlib.path import Path as MplPath
from datetime import datetime, timedelta
import os

# ================== 可自行修改的路径和文件名前后缀 ==================
input_dir = 'E:/WRF/WRFrun260422/wrfout_04-02_origin'
output_dir = 'E:/WRF/WRFs/rain2604'

file_prefix = 'wrfout_d02_'

# 输出图片名前缀、后缀，可自行修改
png_prefix = 'rainfullreg_'
png_suffix = ''

# txt 输出文件名，可自行修改
txt_output = os.path.join(output_dir, 'regiofull.txt')

# 批量绘图时次：09时到23时
start_time = datetime(2016, 4, 2, 9, 0, 0)
end_time = datetime(2016, 4, 2, 23, 0, 0)

os.makedirs(output_dir, exist_ok=True)
# ===================================================================


def create_shp_polygon_mask(lons, lats, shapefile_path):
    """
    根据 shapefile 面边界生成网格点掩膜。
    返回值为布尔数组，True 表示该 WRF 网格点位于 shp 面内。

    说明：
    1. 该方法以网格中心点是否落在 shp 面内作为判断依据，适合WRF规则网格面积统计；
    2. 若某个网格中心点在 shp 面外，即使落在R矩形范围内，也不会参与5/10/20mm面积统计；
    3. 若需要严格按边界裁切每个网格单元的部分面积，可进一步使用 geopandas/shapely 做精确裁剪。
    """
    points = np.column_stack((lons.ravel(), lats.ravel()))
    shp_mask_flat = np.zeros(points.shape[0], dtype=bool)

    sf_mask = shapefile.Reader(shapefile_path)
    for shp in sf_mask.shapes():
        shp_points = shp.points
        if not shp_points:
            continue

        # 处理多部件 polygon，例如一个 shp 记录中包含多个面
        parts = list(shp.parts) + [len(shp_points)]
        for i in range(len(parts) - 1):
            part_points = shp_points[parts[i]:parts[i + 1]]
            if len(part_points) < 3:
                continue

            polygon_path = MplPath(part_points)
            # radius 设置一个很小的正值，使边界上的点也尽量被算入面内
            shp_mask_flat |= polygon_path.contains_points(points, radius=1e-10)

    return shp_mask_flat.reshape(lons.shape)

# 写入 txt 表头
with open(txt_output, 'w', encoding='utf-8') as f_txt:
    f_txt.write('Time\tPrevious_File\tCurrent_File\tRegionA_mm\tRegionB_mm\tRegionC_mm\tRegionD_mm\tRegionR_mean_mm\tRegionR_max_mm\tRegionR_area_gt_5_km2\tRegionR_area_gt_10_km2\tRegionR_area_gt_20_km2\n')

current_time = start_time

while current_time <= end_time:

    previous_time = current_time - timedelta(hours=1)

    previous_time_str = previous_time.strftime('%Y-%m-%d_%H_%M_%S')
    current_time_str = current_time.strftime('%Y-%m-%d_%H_%M_%S')

    file_path_9 = os.path.join(input_dir, file_prefix + previous_time_str)
    file_path_10 = os.path.join(input_dir, file_prefix + current_time_str)

    # 输出图片名与时次对应，例如 12时：rainfull_12.png
    hour_str = current_time.strftime('%H')
    png_output = os.path.join(output_dir, f'{png_prefix}{hour_str}{png_suffix}.png')

    shapefile_path = 'E:/WRF/ynst.shp'

    if not os.path.exists(file_path_9):
        print(f'文件不存在，跳过：{file_path_9}')
        current_time += timedelta(hours=1)
        continue

    if not os.path.exists(file_path_10):
        print(f'文件不存在，跳过：{file_path_10}')
        current_time += timedelta(hours=1)
        continue

    print(f'Processing: {current_time_str}')
    print(f'Previous file: {file_path_9}')
    print(f'Current file: {file_path_10}')

    # 打开 NetCDF 文件
    ncfile_9 = netCDF4.Dataset(file_path_9, 'r')
    ncfile_10 = netCDF4.Dataset(file_path_10, 'r')
    print("Calculating...")

    # 获取降水变量
    rainc_9 = ncfile_9.variables['RAINC'][:]
    rainsh_9 = ncfile_9.variables['RAINSH'][:]
    rainnc_9 = ncfile_9.variables['RAINNC'][:]

    rainc_10 = ncfile_10.variables['RAINC'][:]
    rainsh_10 = ncfile_10.variables['RAINSH'][:]
    rainnc_10 = ncfile_10.variables['RAINNC'][:]

    # 计算总降水量。Rainc为对流性降水，rainsh为浅对流性降水，rainnc为非对流性降水。
    #只画对流性就把后两者去掉
    total_precip_9 = rainc_9 + rainsh_9 + rainnc_9
    total_precip_10 = rainc_10 + rainsh_10 + rainnc_10

    # 计算两个时间步之间的降水量差（单位：mm）
    precip_diff = total_precip_10[0, :, :] - total_precip_9[0, :, :]

    # 将小于等于0mm的降水量设为白色
    precip_diff = np.where(precip_diff <= 0, np.nan, precip_diff)

    # 将 NaN 替换为 0，避免插值时出错
    precip_diff = nan_to_num(precip_diff, nan=0)

    # 获取经纬度信息并去除时间维度
    lats = ncfile_9.variables['XLAT'][0, :, :]
    lons = ncfile_9.variables['XLONG'][0, :, :]

    # 关闭文件
    ncfile_9.close()
    ncfile_10.close()
    print("Drawing...")

    # ====== 新增：计算三个矩形区域的面平均降水量 ======

    # 定义三个区域的经纬度范围（自行修改）
    regions = {
        "RegionA": {"lat_min": 22.8, "lat_max": 22.9, "lon_min": 103.5, "lon_max": 103.6},
        "RegionB": {"lat_min": 22.8, "lat_max": 22.9, "lon_min": 103.8, "lon_max": 103.9},
        "RegionC": {"lat_min": 22.8, "lat_max": 22.9, "lon_min": 104.0, "lon_max": 104.1},
        "RegionD": {"lat_min": 22.5, "lat_max": 22.6, "lon_min": 103.9, "lon_max": 104.0},
    }

    region_mean_results = {}

    print("\n--- 区域平均降雨量计算 ---")
    for name, bounds in regions.items():
        # 根据经纬度范围筛选
        mask = (
            (lats >= bounds["lat_min"]) & (lats <= bounds["lat_max"]) &
            (lons >= bounds["lon_min"]) & (lons <= bounds["lon_max"])
        )

        # 提取该区域的降雨值
        region_values = precip_diff[mask]

        # 去掉NaN
        valid_values = region_values[~np.isnan(region_values)]

        if valid_values.size > 0:
            mean_precip = np.mean(valid_values)
            region_mean_results[name] = mean_precip
            print(f"{name}: 平均降水量 = {mean_precip:.2f} mm")
        else:
            region_mean_results[name] = np.nan
            print(f"{name}: 无有效网格点或数据为空")
    print("------------------------------------\n")

    # ====== 新增：计算R区域的面平均、最大降雨量及强降雨面积 ======
    region_r_bounds = {"lat_min": 22.0, "lat_max": 23.5, "lon_min": 102.5, "lon_max": 105.5}

    r_rect_mask = (
        (lats >= region_r_bounds["lat_min"]) & (lats <= region_r_bounds["lat_max"]) &
        (lons >= region_r_bounds["lon_min"]) & (lons <= region_r_bounds["lon_max"])
    )

    # 关键修改：叠加 shp 面内掩膜，只统计 shp 面内且位于R区域矩形范围内的网格点
    # 最终用于强降雨面积统计的范围 = R矩形范围 ∩ shp面范围
    shp_inside_mask = create_shp_polygon_mask(lons, lats, shapefile_path)
    r_mask = r_rect_mask & shp_inside_mask

    # 根据经纬度估算每个WRF网格的面积，单位km2
    # 近似公式：纬向1度约111.32km，经向1度约111.32*cos(lat)km
    lat_1d = lats[:, 0]
    lon_1d = lons[0, :]

    if lat_1d.size > 1:
        dlat = np.nanmean(np.abs(np.diff(lat_1d)))
    else:
        dlat = 0

    if lon_1d.size > 1:
        dlon = np.nanmean(np.abs(np.diff(lon_1d)))
    else:
        dlon = 0

    deg2km = 111.32
    grid_area = (dlat * deg2km) * (dlon * deg2km * np.cos(np.deg2rad(lats)))

    r_values = precip_diff[r_mask]
    r_area = grid_area[r_mask]
    r_valid_mask = ~np.isnan(r_values)

    print(f"RegionR矩形范围内网格数: {np.sum(r_rect_mask)}")
    print(f"RegionR与shp面相交后参与面积统计网格数: {np.sum(r_mask)}")

    if np.any(r_valid_mask):
        r_valid_values = r_values[r_valid_mask]
        r_valid_area = r_area[r_valid_mask]

        region_r_mean = np.nanmean(r_valid_values)
        region_r_max = np.nanmax(r_valid_values)
        region_r_area_gt_5 = np.sum(r_valid_area[r_valid_values > 5])
        region_r_area_gt_10 = np.sum(r_valid_area[r_valid_values > 10])
        region_r_area_gt_20 = np.sum(r_valid_area[r_valid_values > 20])

        print(f"RegionR: 平均降水量 = {region_r_mean:.2f} mm")
        print(f"RegionR: 最大降水量 = {region_r_max:.2f} mm")
        print(f"RegionR: 5mm以上面积 = {region_r_area_gt_5:.2f} km2")
        print(f"RegionR: 10mm以上面积 = {region_r_area_gt_10:.2f} km2")
        print(f"RegionR: 20mm以上面积 = {region_r_area_gt_20:.2f} km2")
    else:
        region_r_mean = np.nan
        region_r_max = np.nan
        region_r_area_gt_5 = np.nan
        region_r_area_gt_10 = np.nan
        region_r_area_gt_20 = np.nan
        print("RegionR: 无有效网格点或数据为空")

    # 将该时次四个区域平均降雨量和R区域统计结果写入 txt 表格
    with open(txt_output, 'a', encoding='utf-8') as f_txt:
        f_txt.write(
            f"{current_time.strftime('%Y-%m-%d %H:00')}\t"
            f"{os.path.basename(file_path_9)}\t"
            f"{os.path.basename(file_path_10)}\t"
            f"{region_mean_results['RegionA']:.2f}\t"
            f"{region_mean_results['RegionB']:.2f}\t"
            f"{region_mean_results['RegionC']:.2f}\t"
            f"{region_mean_results['RegionD']:.2f}\t"
            f"{region_r_mean:.2f}\t"
            f"{region_r_max:.2f}\t"
            f"{region_r_area_gt_5:.2f}\t"
            f"{region_r_area_gt_10:.2f}\t"
            f"{region_r_area_gt_20:.2f}\n"
        )

    # 经纬度范围
    lat_min, lat_max = 21.99, 24.01
    lon_min, lon_max = 102.49, 106.01

    # 插值处理，使图像更加平滑
    lon_flat = lons.flatten()
    lat_flat = lats.flatten()
    precip_flat = precip_diff.flatten()
    lon_grid, lat_grid = np.meshgrid(np.linspace(lon_min, lon_max, 500), np.linspace(lat_min, lat_max, 500))

    # 插值,cubic方法效果更好
    precip_interp = griddata((lon_flat, lat_flat), precip_flat, (lon_grid, lat_grid), method='cubic')
    #precip_interp = griddata((lon_flat, lat_flat), precip_flat, (lon_grid, lat_grid), method='linear')


    # 打印最小最大降水量，检查插值后的结果
    print("Min precipitation value after interpolation:", np.nanmin(precip_interp))
    print("Max precipitation value after interpolation:", np.nanmax(precip_interp))

    # 手动设置颜色映射，降水量范围和对应颜色
    from matplotlib.colors import ListedColormap, BoundaryNorm
    colors = [
        '#ffffff',  # <0.1mm 白色
        '#d0f0c0', '#a8e08f', '#76cc62', '#4c9a36', '#2b8f14',  # 0.1-10mm: 浅绿到深绿
        '#a0c9e7', '#74b9c8', '#48a1a9', '#1f8a8a', '#006d6d',  # 10-25mm: 浅蓝到深蓝
        '#ffb6c1', '#ff90c4', '#ff6bb8', '#ff47ab', '#ff229e',  # 25-50mm: 粉色
        '#9b2e87'  # >50mm: 紫色
    ]
    levels = [0, 0.1, 2, 4, 6, 8, 10, 15, 20, 25, 30, 40, 50, 100]
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(levels, len(levels) - 1)

    # 绘制填色图
    fig = plt.figure(figsize=(12, 7), dpi=400)
    ax = fig.add_subplot(111, projection=ccrs.PlateCarree())

    c = ax.pcolormesh(lon_grid, lat_grid, precip_interp, cmap=cmap, norm=norm)

    # 添加横向底部色标，调整大小
    cbar = plt.colorbar(c, ax=ax, orientation='horizontal', pad=0.05, shrink=0.8)
    cbar.set_label('Precipitation (mm)', labelpad=5)
    cbar.set_ticks(levels)

    # ====== 新增：在图上绘制三个红色矩形区域 ======
    from matplotlib.patches import Rectangle

    # 与前面计算平均降水量时使用的区域保持一致
    regions = {
        "A": {"lat_min": 22.8, "lat_max": 22.9, "lon_min": 103.5, "lon_max": 103.6},
        "B": {"lat_min": 22.8, "lat_max": 22.9, "lon_min": 103.8, "lon_max": 103.9},
        "C": {"lat_min": 22.8, "lat_max": 22.9, "lon_min": 104.0, "lon_max": 104.1},
        "D": {"lat_min": 22.5, "lat_max": 22.6, "lon_min": 103.9, "lon_max": 104.0},
    }

    for name, bounds in regions.items():
        width = bounds["lon_max"] - bounds["lon_min"]
        height = bounds["lat_max"] - bounds["lat_min"]
        rect = Rectangle(
            (bounds["lon_min"], bounds["lat_min"]),
            width,
            height,
            linewidth=1.5,
            edgecolor='red',
            facecolor='none',
            transform=ccrs.PlateCarree(),
            zorder=10
        )
        ax.add_patch(rect)
        # 添加区域名称标签（可选）
        ax.text(bounds["lon_min"] - 0.02,
                bounds["lat_max"] - 0.02,
                name,
                color='red',
                fontsize=22,
                fontweight='ultralight',   # ← 让字体更纤细
                ha='center',
                va='bottom',
                transform=ccrs.PlateCarree(),
                zorder=11)


    # 绘制云南省边界，指定编码
    #sf = shapefile.Reader(shapefile_path, encoding='GBK')
    sf = shapefile.Reader(shapefile_path)
    for shape in sf.shapeRecords():
        xy = shape.shape.points
        x = [point[0] for point in xy]
        y = [point[1] for point in xy]
        ax.plot(x, y, color='black', linewidth=0.7)

    # 设置经纬度范围
    ax.set_extent([lon_min, lon_max, lat_min, lat_max])


    # 添加经纬度网格，仅右侧和顶部显示
    gridlines = ax.gridlines(draw_labels=True, linestyle='--', color='gray', alpha=0.5)
    gridlines.right_labels = True
    gridlines.top_labels = True
    gridlines.left_labels = False
    gridlines.bottom_labels = False

    # 设置经纬度间隔，比如经度 0.5°，纬度 0.5°
    gridlines.xlocator = mticker.FixedLocator(np.arange(70, 141, 1.0))  # 经度
    gridlines.ylocator = mticker.FixedLocator(np.arange(10, 51, 1.0))   # 纬度

    # 设置标签样式
    gridlines.xlabel_style = {'size': 20, 'color': 'black'}
    gridlines.ylabel_style = {'size': 20, 'color': 'black'}


    # 添加标题
    #ax.set_title('Hourly Precipitation in Simulated Area', fontsize=14)

    # 输出图片
    plt.savefig(png_output, dpi=400)
    plt.close(fig)

    print(f"Finished: {png_output}")

    current_time += timedelta(hours=1)

print("All Finished!")
print(f"区域平均降雨量表格已保存到: {txt_output}")