import numpy as np
import matplotlib.pyplot as plt
from selenium.webdriver.support.wait import WebDriverWait
from skimage import io, color, filters
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import os
import folium


def start_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=chrome_options)


def capture_map_image(map_path, save_path):
    driver = start_driver()
    try:
        driver.get(f"file:///{map_path}")
        # Daha kısa timeout ve basit bekleme
        WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.CLASS_NAME, "leaflet-tile"))
        )
        time.sleep(2)
        driver.save_screenshot(save_path)
    except Exception as e:
        print(f"Hata: {e}")
        # Hata durumunda da ekran görüntüsü almaya çalış
        try:
            time.sleep(3)
            driver.save_screenshot(save_path)
        except:
            pass
    finally:
        driver.quit()


def load_image(image_path):
    image = io.imread(image_path)
    if image.shape[2] == 4:
        image = image[:, :, :3]
    gray_image = color.rgb2gray(image)
    return gray_image


def binarize_image(gray_image):
    threshold = filters.threshold_otsu(gray_image)
    return gray_image > threshold


def fractal_dimension(Z, threshold=0.9):
    assert len(Z.shape) == 2

    def boxcount(Z, k):
        S = np.add.reduceat(
            np.add.reduceat(Z, np.arange(0, Z.shape[0], k), axis=0),
            np.arange(0, Z.shape[1], k), axis=1)
        return len(np.where((S > 0) & (S < k * k))[0])

    Z = (Z < threshold)
    p = min(Z.shape)
    n = 2 ** np.floor(np.log(p) / np.log(2))
    n = int(np.log(n) / np.log(2))
    sizes = 2 ** np.arange(n, 1, -1)
    counts = [boxcount(Z, size) for size in sizes]
    coeffs = np.polyfit(np.log(sizes), np.log(counts), 1)
    return -coeffs[0]


# sadece R (yağış) ve K (toprak türü) alınır, fraktal boyutla birlikte A hesaplanır
def rusle_simplified_assessment(fractal_dimension, soil_type, rainfall):
    K_values = {
        "kumlu": 0.45,
        "siltli": 0.50,
        "killi": 0.35,
        "çakıllı": 0.30,
        "organik": 0.20,
        "azotlu": 0.25
    }

    R = rainfall
    K = K_values.get(soil_type, 0.4)

    # Fraktal boyutu LS faktörü yerine çarpan gibi dahil ediyoruz
    A = (R*0.1) * K * (fractal_dimension / 2.5)

    if A > 30:
        risk_level = "Yüksek"
    elif A > 10:
        risk_level = "Orta"
    else:
        risk_level = "Düşük"

    return risk_level, A


def suggest_tree_species(soil_type):
    tree_suggestions = {
        "kumlu": ["Çam (Pinus spp.)"],
        "siltli": ["Meşe (Quercus spp.)"],
        "killi": ["Ihlamur (Tilia spp.)"],
        "çakıllı": ["Karaçam (Pinus nigra)"],
        "azotlu": ["Fıstık Çamı (Pinus brutia)"],
        "organik": ["Kayın (Fagus sylvatica)"]
    }
    return tree_suggestions.get(soil_type, ["Çam", "Servi"])


def create_map(latitude, longitude):
    map_center = [latitude, longitude]
    mymap = folium.Map(location=map_center, zoom_start=18, control_scale=True)

    folium.TileLayer(
        'Esri.WorldImagery',
        attr='Tiles © Esri & contributors'
    ).add_to(mymap)

    folium.Circle(
        location=map_center,
        radius=5000,
        color="blue",
        fill=True,
        fill_color="blue",
        fill_opacity=0.1
    ).add_to(mymap)

    map_path = os.path.join(os.getcwd(), "harita.html")
    mymap.save(map_path)
    return map_path


def main():
    print("Lütfen enlem ve boylam bilgilerini girin:")
    latitude = float(input("Enlem: "))
    longitude = float(input("Boylam: "))

    print("Toprak türünü seçin (kumlu, siltli, killi, çakıllı, azotlu, organik):")
    soil_type = input("Toprak türü: ")

    print("Yıllık ortalama yağış miktarını girin (mm/yıl):")
    rainfall = float(input("Yağış: "))

    map_path = create_map(latitude, longitude)
    print(f"Harita kaydedildi: {map_path}")

    screenshot_path = "screenshot.png"
    capture_map_image(map_path, screenshot_path)
    print(f"Ekran görüntüsü alındı: {screenshot_path}")

    gray_image = load_image(screenshot_path)
    binary_image = binarize_image(gray_image)
    fd = fractal_dimension(binary_image)
    print(f"Fraktal Boyut: {fd:.2f}")

    risk_level, erosion_amount = rusle_simplified_assessment(fd, soil_type, rainfall)
    print(f"Erozyon Riski: {risk_level}")
    # print(f"Hesaplanan Erozyon (basitleştirilmiş skor): {erosion_amount:.2f}")

    tree_species = suggest_tree_species(soil_type)
    print(f'Önerilen Ağaç Türleri: {tree_species}')

    plt.figure(figsize=(10, 5))
    plt.subplot(1, 2, 1)
    plt.imshow(gray_image, cmap='gray')
    plt.title('Gri Tonlama Görüntüsü')
    plt.axis('off')
    plt.subplot(1, 2, 2)
    plt.imshow(binary_image, cmap='gray')
    plt.title(f'İkili Görüntü (FB: {fd:.2f})')
    plt.axis('off')
    plt.show()


if __name__ == "__main__":
    main()
