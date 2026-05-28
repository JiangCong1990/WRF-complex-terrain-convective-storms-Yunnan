#适用于打开V格式多普勒雷达

import cinrad
import cartopy
from cinrad.visualize import PPI
import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader
import numpy as np
import matplotlib.pyplot as plt
import datetime

# 忽略警告
import warnings
warnings.filterwarnings("ignore")

# 读取数据
basePath = "E:/radread/"
nFiles = basePath + "2016040302.51V"
f = cinrad.io.read_auto(nFiles)

#雷达站名称和经纬度
f.name = "WENSHAN"
f.code = "Z9876"
f.stationlat = 23.46
f.stationlon = 104.24

print("Calculating...")

#修正时间日期（数据默认是世界时）
f.scantime = f.scantime + datetime.timedelta(hours=15708368)
data = f.get_data(0, 230, "REF")  # 读取第一层的反射率
rl = list(f.iter_tilt(230, "REF"))
cr = cinrad.calc.quick_cr(rl) #计算组合反射率
velo = f.get_data(0, 230, "VEL")  #读取速度
r2 = list(f.iter_tilt(230, "VEL")) 

print("Drawing...")

# 创建PPI对象
#地名文件在 E:\Program Files\Python311\Lib\site-packages\cinrad\data\chinaCity.json
#1 画组合反射率
fig = PPI(cr, dpi=400, style="white", extent=[102.5, 105, 22, 23.6], add_city_names=False)  # 使用白色背景

#2 画速度图
#fig = PPI(velo, dpi=400, style="white", extent=[102.5, 105, 22, 23.6], add_city_names=False)

# 附加操作
fig.plot_range_rings([30, 60, 90, 120, 150], color="gray", linewidth=1)  # 用这个来画圈

# 设置经纬网间隔 最后一个数字
grid_extent = [102.5, 106, 22.0, 24.0]
xlocs = np.arange(np.ceil(grid_extent[0]), np.floor(grid_extent[1]) + 1, 1)
ylocs = np.arange(np.ceil(grid_extent[2]), np.floor(grid_extent[3]) + 1, 1)

gl = fig.gridlines(
    draw_labels=False,
    xlocs=xlocs,
    ylocs=ylocs,
    linewidth=1,
    color="lightgray",
    xlabel_style={"size": 36},
    ylabel_style={"size": 36}
)  # 用这个来画经纬度网格线


print("Still drawing...")

#下方绘制VCS横截面
#vcs = cinrad.calc.VCS(rl)  #这是强度截面
#vcs = cinrad.calc.VCS(r2)    #这是速度截面

#剖面绘图
#sec = vcs.get_section(start_cart=(104.35, 23.03), end_cart=(104.8, 22.98))  # 传入经纬度坐标
#sec = vcs.get_section(start_polar=(113, 250), end_polar=(114, 28)) # 传入极坐标
#fig.plot_cross_section(sec, linecolor="red") #绘制剖面线

# 保存图像
fig("E:/radread/160402wsnew/new/WSH51_030251.png")
print("Finished")
