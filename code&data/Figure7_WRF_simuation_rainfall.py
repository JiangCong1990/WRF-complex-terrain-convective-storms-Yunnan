import netCDF4
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import shapefile
from scipy.interpolate import griddata
from numpy import nan_to_num
import matplotlib.ticker as mticker

# 文件路径设置
file_path_9 = 'E:/WRF/WRFrun926/geo_origin/wrfout_d02_2016-04-02_11_00_00'
file_path_10 = 'E:/WRF/WRFrun926/geo_origin/wrfout_d02_2016-04-02_17_00_00'
shapefile_path = 'E:/WRF/ynst.shp'

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
        print(f"{name}: 平均降水量 = {mean_precip:.2f} mm")
    else:
        print(f"{name}: 无有效网格点或数据为空")
print("------------------------------------\n")




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
plt.savefig('E:/WRF/WRFs/rain/raincFull_6h.png', dpi=400)
print("Finished")
