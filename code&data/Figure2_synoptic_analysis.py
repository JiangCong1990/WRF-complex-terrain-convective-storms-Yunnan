#!/usr/bin/env python3
"""
plot_era5_wind_z_with_boxes.py
文件结构可以先用ncsee.py查看

功能：
 - 读取 ERA5 netCDF
 - 选取 对应日期时间的数据
 - 在经纬范围 lat:10-40, lon:87-117 内裁切
 - 对每个 pressure_level (850,700,500,200 hPa) 分别画单张图：
    - 风矢（quiver）
    - 位势高度等值线（黑色）
    - 两个红色矩形框
 - 输出 PNG 文件
"""
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.patches as mpatches
import os
import cartopy.io.shapereader as shpreader
import cartopy.feature as cfeature
from scipy.ndimage import gaussian_filter
import cartopy.feature as cfeature

# -----------------------------
# 用户设置
# -----------------------------
"""设置文件路径、时间、绘图经纬度和输出文件夹"""
nc_file = "E:/WRF/WRFs/era5/data_stream-oper_stepType-instant.nc"  # <-- ERA5 netCDF 文件路径
target_time = np.datetime64("2016-04-02T12:00")
lon_min, lon_max = 87.0, 117.0
lat_min, lat_max = 9.9, 40.1
out_dir = "E:/WRF/WRFs/era0402m"
os.makedirs(out_dir, exist_ok=True)
max_quiver_points = 25
# -----------------------------

def add_red_box(ax, lon_min, lon_max, lat_min, lat_max, **kwargs):
    """在地图上画矩形框"""
    rect = mpatches.Rectangle(
        (lon_min, lat_min),  # 左下角
        lon_max - lon_min,
        lat_max - lat_min,
        linewidth=kwargs.get("linewidth", 1.5),
        edgecolor=kwargs.get("edgecolor", "red"),
        facecolor="none",
        transform=ccrs.PlateCarree(),
        zorder=5,
    )
    ax.add_patch(rect)

def main():
    print("打开文件:", nc_file)
    ds = xr.open_dataset(nc_file)
    for v in ("u", "v", "z"):
        if v not in ds:
            raise KeyError(f"缺少变量 {v}")

    # 选择时间维
    if "valid_time" in ds.coords:
        time_coord = "valid_time"
    elif "time" in ds.coords:
        time_coord = "time"
    else:
        raise KeyError("找不到时间坐标 valid_time 或 time")

    times = ds[time_coord].values
    dt_idx = int(np.argmin(np.abs(times - target_time)))
    chosen_time = np.datetime_as_string(times[dt_idx])
    print(f"选取时间: {chosen_time}")

    ds_t = ds.sel({time_coord: times[dt_idx]})

    ds_box = ds_t.sel(
        longitude=slice(lon_min, lon_max),
        latitude=slice(lat_max, lat_min)
        if ds_t.latitude[0] > ds_t.latitude[-1]
        else slice(lat_min, lat_max),
    )

    g = 9.80665
    plevs = ds_box["pressure_level"].values

    for p in plevs:
        print(f"绘制 {p} hPa")
        u = ds_box["u"].sel(pressure_level=p).squeeze()
        v = ds_box["v"].sel(pressure_level=p).squeeze()
        z = (ds_box["z"].sel(pressure_level=p) / g).squeeze()

        lons = u["longitude"].values
        lats = u["latitude"].values
        Lon, Lat = np.meshgrid(lons, lats)
        U, V, Z = u.values, v.values, z.values
		
		# ====== 对位势高度做高斯平滑 ======
        Z_smooth = gaussian_filter(Z, sigma=1.2)

        nx, ny = U.shape[1], U.shape[0]
        step_x = 8 #风向间隔修改数字
        step_y = 8 #风向间隔修改数字

        fig = plt.figure(figsize=(8, 8))
        ax = plt.axes(projection=ccrs.PlateCarree())
        ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())

        #ax.coastlines(resolution="10m")
        # ax.add_feature(cfeature.BORDERS.with_scale("10m"), linewidth=0.5)    #国境线有bug，注意有冲突地区不能用！
		# ---- 浅黄色陆地填充（淡到不影响主图） ----
        ax.add_feature(
            cfeature.LAND.with_scale("10m"),
            facecolor=(1.0, 0.97, 0.70, 0.6),   # RGBA：浅黄色 + 60%透明度
            edgecolor='none',
            zorder=0
        )

# ---- 浅灰色海岸线 ----
        ax.add_feature(
            cfeature.COASTLINE.with_scale("10m"),
            edgecolor='gray',
            linewidth=0.6,
            zorder=1
        )
        
		# 读取 shapefile画国境线
        shapefile_path = "E:/GISdata/WRF/Chinaboud.shp"  # 替换为你的 shp 文件路径
        reader = shpreader.Reader(shapefile_path)
        china_geoms = list(reader.geometries())

        # 添加到地图
        ax.add_geometries(
            china_geoms,
            crs=ccrs.PlateCarree(),
            edgecolor='darkred',  # 边线颜色
            facecolor='none',   # 只画边线
            linewidth=0.8,
            zorder=6
        )
		
		
		# === 修改后的经纬线标注部分 ===
        gl = ax.gridlines(
            draw_labels=True, 
            x_inline=False, 
            y_inline=False, 
            linewidth=0.5, 
            color='gray', 
            alpha=0.5
		    )
        gl.top_labels = False
        gl.right_labels = False
        gl.xlabel_style = {'size': 18, 'color': 'black'}
        gl.ylabel_style = {'size': 18, 'color': 'black'}
# ===========================
        #画位势高度等值线
        cs = ax.contour(
            Lon, Lat, Z_smooth, levels=12, colors="black", linewidths=1.2, transform=ccrs.PlateCarree()
        )
        ax.clabel(cs, fmt="%d", fontsize=14)

        q = ax.quiver(
            Lon[::step_y, ::step_x],
            Lat[::step_y, ::step_x],
            U[::step_y, ::step_x],
            V[::step_y, ::step_x],
			color='blue',
            transform=ccrs.PlateCarree(),
            scale=400,  #用于调整风向箭头大小
        )
        ax.quiverkey(q, 0.85, 0.05, 20, "20 m/s", labelpos="E",coordinates='axes',fontproperties={'size': 14})

        # 添加文字标注
        ax.text(87, 14, "Bay of Bengal", color="black", fontsize=18, fontweight="ultralight", transform=ccrs.PlateCarree(), zorder=10)
        ax.text(105, 20, "Beibu Gulf", color="black", fontsize=18, fontweight="ultralight", transform=ccrs.PlateCarree(), zorder=10)
        ax.text(87, 30, "Tibetan Plateau", color="black", fontsize=18, fontweight="ultralight", transform=ccrs.PlateCarree(), zorder=10)
        ax.text(97, 15, "Indochinese Peninsula", color="black", fontsize=18, fontweight="ultralight", transform=ccrs.PlateCarree(), zorder=10)

        # === 添加两个红色矩形框 ===
        add_red_box(ax, 97, 107, 20, 30)           # 框1
        add_red_box(ax, 102.5, 106, 22, 24)        # 框2

        #ax.set_title(f"ERA5 {int(p)} hPa 风场与位势高度\nTime: {chosen_time}")
		#修改输出文件名
        outfn = os.path.join(out_dir, f"era5_20160402_12z_{int(p)}hPa_box.png")  #输出文件名
        plt.savefig(outfn, dpi=300, bbox_inches="tight")
        plt.close(fig)
        print("保存:", outfn)

    print("✅ 全部完成，输出目录:", out_dir)

if __name__ == "__main__":
    main()
