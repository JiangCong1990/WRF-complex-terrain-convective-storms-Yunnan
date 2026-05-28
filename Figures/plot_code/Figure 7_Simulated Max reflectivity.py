import numpy as np
import matplotlib.pyplot as plt
import netCDF4 as nc
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import shapefile
from matplotlib.colors import ListedColormap, BoundaryNorm
import matplotlib.ticker as mticker
from datetime import datetime, timedelta
import os

# ================== 可自行修改的路径和文件名前后缀 ==================
input_dir = "E:/WRF/WRFrun260422/wrfout_04-02_2000"
output_dir = "E:/WRF/WRFs/rad2604"

file_prefix = "wrfout_d02_"
out_prefix = "radnewnone_"
out_suffix = ""

start_time = datetime(2016, 4, 2, 0, 0, 0)
end_time = datetime(2016, 4, 3, 12, 0, 0)

txt_output = os.path.join(output_dir, "max_reflectivity_table_none.txt")

os.makedirs(output_dir, exist_ok=True)
# ===================================================================

# 先写入txt表头
with open(txt_output, "w", encoding="utf-8") as f_txt:
    f_txt.write("Hour_Index\tFile_Name\tMax_dBZ\tLatitude\tLongitude\n")

current_time = start_time
hour_index = 0

while current_time <= end_time:

    time_str = current_time.strftime("%Y-%m-%d_%H_%M_%S")
    file_path = os.path.join(input_dir, file_prefix + time_str)

    # 输出图片名：前缀 + 小时序号 + 后缀
    png_name = f"{out_prefix}{hour_index:02d}{out_suffix}.png"
    png_path = os.path.join(output_dir, png_name)

    if not os.path.exists(file_path):
        print(f"文件不存在，跳过：{file_path}")
        with open(txt_output, "a", encoding="utf-8") as f_txt:
            f_txt.write(f"{hour_index:02d}\t{os.path.basename(file_path)}\tNaN\tNaN\tNaN\n")
        current_time += timedelta(hours=1)
        hour_index += 1
        continue

    print(f"Processing: {file_path}")

    # 读取NetCDF数据
    dataset = nc.Dataset(file_path)
    shapefile_path = 'E:/WRF/ynst.shp'

    # 检查 REFLECTIVITY 数据维度
    print(dataset.variables["REFL_10CM"].shape)  # 查看维度 (time, levels, lat, lon)
    print("Calculating...")

    # 提取雷达反射率和经纬度数据（选取时间=0，层=0）
    reflectivity = dataset.variables["REFL_10CM"][0, 0, :, :]  # 第一个时间步，第一个垂直层
    lats = dataset.variables["XLAT"][0, :, :]
    lons = dataset.variables["XLONG"][0, :, :]

    # 定义经纬度范围
    lat_min, lat_max = 21.99, 24.01
    lon_min, lon_max = 102.49, 106.01
    #lat_min, lat_max = 21.49, 25.01
    #lon_min, lon_max = 100.49, 106.51

    # ===== 新增：提取绘图区域内的最大反射率 =====
    region_mask = (lats >= lat_min) & (lats <= lat_max) & (lons >= lon_min) & (lons <= lon_max)

    # 如果 reflectivity 是 masked array，建议用压缩后的有效值计算
    region_reflectivity = reflectivity[region_mask]
    region_lats = lats[region_mask]
    region_lons = lons[region_mask]

    # 统一转换，避免 masked array 的 mask 只有一个 False 导致索引长度不一致
    region_reflectivity_data = np.ma.filled(region_reflectivity, np.nan)
    region_lats_data = np.ma.filled(region_lats, np.nan)
    region_lons_data = np.ma.filled(region_lons, np.nan)

    valid_mask = (
        ~np.isnan(region_reflectivity_data) &
        ~np.isnan(region_lats_data) &
        ~np.isnan(region_lons_data)
    )

    valid_region_reflectivity = region_reflectivity_data[valid_mask]
    valid_region_lats = region_lats_data[valid_mask]
    valid_region_lons = region_lons_data[valid_mask]

    if valid_region_reflectivity.size > 0:
        max_idx = np.argmax(valid_region_reflectivity)

        region_max = valid_region_reflectivity[max_idx]
        region_max_lat = valid_region_lats[max_idx]
        region_max_lon = valid_region_lons[max_idx]

        print(f"Maximum value of the area: {region_max:.2f} dBZ")
        print(f"Location of maximum value: lat = {region_max_lat:.3f}, lon = {region_max_lon:.3f}")

        with open(txt_output, "a", encoding="utf-8") as f_txt:
            f_txt.write(
                f"{hour_index:02d}\t{os.path.basename(file_path)}\t"
                f"{region_max:.2f}\t{region_max_lat:.3f}\t{region_max_lon:.3f}\n"
            )
    else:
        print("绘图区域内没有有效的反射率数据。")
        with open(txt_output, "a", encoding="utf-8") as f_txt:
            f_txt.write(f"{hour_index:02d}\t{os.path.basename(file_path)}\tNaN\tNaN\tNaN\n")
    # ===== 新增结束 =====

    # 定义Cinrad雷达反射率色标（中国气象局风格）
    ref_colors = [
        "#0000FF", "#1ca1ed", "#00FFFF", "#05f52d", "#04c704", "#008000", "#FFFF00", "#FFD700",
        "#FFA500", "#FF0000", "#d60202", "#8B0000", "#FF00FF", "#800080", "#9370DB"
    ]
    ref_levels = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75]  #已修正色标错误
    cmap = ListedColormap(ref_colors)
    norm = BoundaryNorm(ref_levels, cmap.N)
    print("Drawing...")

    # 创建绘图
    plt.figure(figsize=(10, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent([lon_min, lon_max, lat_min, lat_max])

    # 添加地图要素
    #ax.add_feature(cfeature.BORDERS, linestyle='--')
    ax.add_feature(cfeature.COASTLINE)
    #ax.add_feature(cfeature.STATES, linestyle=':')

    # 绘制云南省边界，指定编码
    #sf = shapefile.Reader(shapefile_path, encoding='GBK')
    sf = shapefile.Reader(shapefile_path)
    for shape in sf.shapeRecords():
        xy = shape.shape.points
        x = [point[0] for point in xy]
        y = [point[1] for point in xy]
        ax.plot(x, y, color='black', linewidth=0.7)

    # 绘制雷达反射率
    c = plt.contourf(lons, lats, reflectivity, levels=ref_levels, cmap=cmap, norm=norm, transform=ccrs.PlateCarree())

    # 添加经纬度网格，仅右侧和顶部显示
    gridlines = ax.gridlines(draw_labels=True, linestyle='--', color='gray', alpha=0.5)
    gridlines.right_labels = False
    gridlines.top_labels = True
    gridlines.left_labels = True
    gridlines.bottom_labels = False

    # 设置经纬度间隔，比如经度 0.5°，纬度 0.5°
    gridlines.xlocator = mticker.FixedLocator(np.arange(70, 141, 1.0))  # 经度
    gridlines.ylocator = mticker.FixedLocator(np.arange(10, 51, 1.0))   # 纬度

    # 设置标签样式
    gridlines.xlabel_style = {'size': 20, 'color': 'black'}
    gridlines.ylabel_style = {'size': 20, 'color': 'black'}

    # 添加色标
    cb = plt.colorbar(c, orientation='vertical', shrink=0.5, pad=0.02)
    #cb.set_label('Simulated Radar Reflectivity (dBZ)')

    # 添加标题
    #plt.title('Local Time 04:00, 3rd Apr. 2016')

    # 保存图像到文件
    plt.savefig(png_path, dpi=200)

    # 显示图像
    #plt.show()
    plt.close()
    dataset.close()

    print(f"Finished: {png_path}")

    current_time += timedelta(hours=1)
    hour_index += 1

print("All Finished!")
print(f"Maximum reflectivity table saved to: {txt_output}")