import netCDF4 as nc
import numpy as np
import matplotlib.pyplot as plt
import os

# ======================
# 1. 读取 WRF 输出文件
# ======================
file_path = "E:/WRF/WRFrun260422/wrfout_04-02_2000/wrfout_d02_2016-04-02_15_00_00"
ds = nc.Dataset(file_path)

# ======================
# 2. 读取变量
# ======================
# WRF 中的 W 是交错网格，需要取中点
W = ds.variables["W"][:]        # (Time, bottom_top_stag, south_north, west_east)
PH = ds.variables["PH"][:]      # 位势
PHB = ds.variables["PHB"][:]    # 基本态位势
HGT = ds.variables["HGT"][:]    # 地形
XLAT = ds.variables["XLAT"][:]
XLONG = ds.variables["XLONG"][:]

# ======================
# 3. 计算几何高度 (m)
# ======================
g = 9.81
z_stag = (PH + PHB) / g
z = 0.5 * (z_stag[:, :-1, :, :] + z_stag[:, 1:, :, :])

# ======================
# 4. 垂直速度插值到质量点
# ======================
w = 0.5 * (W[:, :-1, :, :] + W[:, 1:, :, :])

# 取第一个时次
z = z[0]
w = w[0]
ter = HGT[0]
lats = XLAT[0]
lons = XLONG[0]

# ======================
# 5. 找 22.7°N
# ======================
target_lat = 23.37
lat_1d = lats[:, 0]
lat_idx = np.argmin(np.abs(lat_1d - target_lat))

# ======================
# 6. 经度范围
# ======================
lon_min = 102.47
lon_max = 106.03
lon_1d = lons[0, :]
lon_idx = np.where((lon_1d >= lon_min) & (lon_1d <= lon_max))[0]

# ======================
# 7. 提取剖面
# ======================
w_cs = w[:, lat_idx, lon_idx]
z_cs = z[:, lat_idx, lon_idx]
ter_cs = ter[lat_idx, lon_idx]
lon_cs = lon_1d[lon_idx]

# ======================
# 8. 作图（填色剖面 + 统一色标）
# ======================
plt.figure(figsize=(12, 6))

# 构造 2D 经度数组
lon_2d = np.tile(lon_cs, (z_cs.shape[0], 1))

# 固定色标范围
vmin, vmax = -5.0, 5.0
levels = np.linspace(vmin, vmax, 41)

# —— 填色：垂直速度
cf = plt.contourf(
    lon_2d,
    z_cs,
    w_cs,
    levels=levels,
    cmap="coolwarm",
    vmin=vmin,
    vmax=vmax,
    extend="both"
)

# —— 0 m/s 等值线
plt.contour(
    lon_2d,
    z_cs,
    w_cs,
    levels=[0],
    colors="black",
    linewidths=0.6
)

# —— 地形
plt.fill_between(lon_cs, ter_cs, 0, color="gray")

# ======================
# 图形设置（优化版）
# ======================
plt.xlabel("Longitude (°E)", fontsize=14)
plt.ylabel("Height (m)", fontsize=14)

# 限制高度到 8 km
plt.ylim(0, 8000)

# 坐标刻度字体
plt.xticks(fontsize=16)
plt.yticks(fontsize=16)

plt.grid(ls="--", alpha=0.4)

# ======================
# 色标（底部）
# ======================
cbar = plt.colorbar(
    cf,
    ax=plt.gca(),
    orientation="horizontal",
    pad=0.12,
    aspect=40
)
cbar.set_label("Vertical Velocity (m s$^{-1}$)")


# ======================
# 9. 输出
# ======================
out_dir = "E:/WRF/WRFs/verti2604"
os.makedirs(out_dir, exist_ok=True)

out_png = os.path.join(out_dir, "Vertiv_37non15.png")
plt.savefig(out_png, dpi=300, bbox_inches="tight")
plt.close()

print("输出完成：", out_png)
