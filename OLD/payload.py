import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_cross(ax, x, y, size=10, color='#00BFFF'):
    # Vẽ dấu cộng với tâm (x, y), size là cạnh mỗi nhánh
    # trung tâm
    ax.add_patch(patches.Rectangle((x-size/2, y-size/2), size, size, color=color))
    # nhánh ngang trái
    ax.add_patch(patches.Rectangle((x-3*size/2, y-size/2), size, size, color=color))
    # nhánh ngang phải
    ax.add_patch(patches.Rectangle((x+size/2, y-size/2), size, size, color=color))
    # nhánh dọc trên
    ax.add_patch(patches.Rectangle((x-size/2, y+size/2), size, size, color=color))
    # nhánh dọc dưới
    ax.add_patch(patches.Rectangle((x-size/2, y-3*size/2), size, size, color=color))

def main():
    fig, ax = plt.subplots(figsize=(7,7))
    plt.xlim(0, 100)
    plt.ylim(0, 100)
    ax.set_aspect('equal')

    size = 10  # mỗi nhánh/tâm dấu cộng 10cm
    pitch = 20 # khoảng cách giữa hai tâm liên tiếp xếp khít (vì nhánh kề nhánh)

    # Xếp dấu cộng khít cạnh, bắt đầu từ (size/2, size/2), đáp ứng điều kiện không vượt ra ngoài biên
    count_x = int((100 - size) // pitch) + 1
    count_y = int((100 - size) // pitch) + 1

    for i in range(count_x):
        for j in range(count_y):
            x = size/2 + i*pitch
            y = size/2 + j*pitch
            # Đảm bảo dấu cộng không vượt ra ngoài vật liệu 1mx1m
            if (x - 1.5*size >= 0) and (x + 1.5*size <= 100) and (y - 1.5*size >= 0) and (y + 1.5*size <= 100):
                draw_cross(ax, x, y, size=size, color='#00BFFF')

    # Viền vật liệu
    ax.add_patch(patches.Rectangle((0,0), 100, 100, fill=False, lw=2, ls='-', color='black'))
    # Lưới chia 10cm
    ax.set_xticks(range(0, 101, 10))
    ax.set_yticks(range(0, 101, 10))
    ax.grid(True, color='lightgray', ls=":")

    ax.set_xlabel("cm")
    ax.set_ylabel("cm")
    plt.title("Cách xếp dấu cộng sát cạnh tối ưu trên tấm vật liệu 1m x 1m")
    plt.tight_layout()
    plt.show()
if __name__ == "__main__":
    main()