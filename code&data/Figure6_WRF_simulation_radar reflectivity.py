import numpy as np
import matplotlib.pyplot as plt
import netCDF4 as nc
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import shapefile
from matplotlib.colors import ListedColormap, BoundaryNorm
import matplotlib.ticker as mticker

# 读取NetCDF数据
file_path = "E:/WRF/WRFrun926/geo_2000/wrfout_d02_2016-04-02_20_00_00"
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

# 定义Cinrad雷达反射率色标（中国气象局风格）
ref_colors = [
    "#0000FF", "#1ca1ed", "#00FFFF", "#05f52d", "#04c704", "#008000", "#FFFF00", "#FFD700",
    "#FFA500", "#FF0000", "#d60202", "#8B0000", "#FF00FF", "#800080", "#9370DB"
]
ref_levels = [0, 5, 10, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80]
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
plt.savefig("E:/WRF/WRFs/rad/radnone_20.png", dpi=200)

# 显示图像
plt.show()
