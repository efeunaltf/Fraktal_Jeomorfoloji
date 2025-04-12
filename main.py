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
import keyboard



# Selenium'da headless modda tarayıcıyı başlatmak için ayarlama
def start_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Headless (arka planda) mod
    driver = webdriver.Chrome(options=chrome_options)
    return driver

# Folium haritası HTML'sinin ekran görüntüsünü almak
def capture_map_image(map_path, save_path):
    driver = start_driver()

    # HTML dosyasını aç
    driver.get(f"file:///{map_path}")

    # Sayfanın yüklenmesini bekle

    try:
        # Sayfadaki belirli bir HTML elemanının yüklenmesini bekle (Örneğin, harita div'i)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "leaflet-tile"))
        )
    except Exception as e:
        print("Harita yüklenirken hata oluştu:", e)

    # Ekran görüntüsünü al
    time.sleep(2)
    driver.save_screenshot(save_path)
    driver.quit()

# Görsel işleme ve fraktal boyutu hesaplama
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
    # Sadece 2D görüntüler için
    assert len(Z.shape) == 2

    def boxcount(Z, k):
        S = np.add.reduceat(
            np.add.reduceat(Z, np.arange(0, Z.shape[0], k), axis=0),
            np.arange(0, Z.shape[1], k), axis=1)

        return len(np.where((S > 0) & (S < k*k))[0])

    Z = (Z < threshold)
    p = min(Z.shape)
    n = 2**np.floor(np.log(p)/np.log(2))
    n = int(np.log(n)/np.log(2))
    sizes = 2**np.arange(n, 1, -1)
    counts = [boxcount(Z, size) for size in sizes]
    coeffs = np.polyfit(np.log(sizes), np.log(counts), 1)
    return -coeffs[0]

# Erozyon riski hesaplama fonksiyonu
def erosion_risk_assessment(fractal_dimension, soil_type, humidity_level, wind_exposure):
    environmental_factors = {
        "kumlu": 0.5,
        "siltli": 0.5,
        "killi": 0.3,
        "çakıllı": 0.3,
        "organik": 0.1,
        "azotlu": 0.1
    }
    humidity_factors = {
        "düşük": 0.4,
        "orta": 0.1,
        "yüksek": 0.4
    }
    wind_factors = {
        "düşük": 0.1,
        "orta": 0.3,
        "yüksek": 0.5
    }

    erosion_risk = fractal_dimension + environmental_factors.get(soil_type) + \
                   humidity_factors.get(humidity_level) + wind_factors.get(wind_exposure)

    if erosion_risk > 2.3:
        return "Yüksek"
    elif erosion_risk > 1.6:
        return "Orta"
    else:
        return "Düşük"

# Ağaç önerileri fonksiyonu
def suggest_tree_species(soil_type):
    tree_suggestions = {
        "kumlu": ["İğde", "Çam", "Akasya"],
        "siltli": ["Söğüt", "Kavak", "Meşe"],
        "killi": ["Ladin", "Ihlamur", "Akçaağaç"],
        "çakıllı": ["Çam", "Sedir", "Karaçam"],
        "azotlu": ["Zeytin", "Fıstık Çamı", "Huş"],
        "organik": ["Kayın", "Çınar", "Meşe"]
    }

    # Risk ve toprak türüne göre ağaç önerileri
    suggestions = tree_suggestions.get(soil_type, [])

    if not suggestions:
        return ["Çam", "Servi"]  # Varsayılan öneri
    return suggestions

# Ana işlev
def main():
    print("Lütfen enlem ve boylam bilgilerini girin:")
    latitude = float(input("Enlem: "))
    longitude = float(input("Boylam: "))

    print("Toprak türünü seçin (kumlu, siltli, killi, çakıllı, azotlu, organik):")
    soil_type = input("Toprak türü: ")

    print("Nem seviyesini seçin (düşük, orta, yüksek):")
    humidity_level = input("Nem seviyesi: ")

    print("Rüzgar maruziyetini seçin (düşük, orta, yüksek):")
    wind_exposure = input("Rüzgar maruziyeti: ")

    # Harita HTML'ini oluşturup kaydediyoruz
    map_path = create_map(latitude, longitude)
    print(f"Harita kaydedildi: {map_path}")

    # Ekran görüntüsünü alıyoruz
    screenshot_path = "screenshot.png"
    capture_map_image(map_path, screenshot_path)
    print(f"Ekran görüntüsü alındı: {screenshot_path}")

    # Görsel işleme
    gray_image = load_image(screenshot_path)
    binary_image = binarize_image(gray_image)
    fd = fractal_dimension(binary_image)
    print(f"Fraktal Boyut: {fd}")



    # Fraktal boyut hesaplama sonuçlarıyla devam
    erosion_risk = erosion_risk_assessment(fd, soil_type, humidity_level, wind_exposure)
    print(f'Erozyon Riski: {erosion_risk}')
    tree_species = suggest_tree_species(soil_type)
    print(f'Önerilen Ağaç Türleri: {tree_species}')

    # Görsel gösterimi
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



# Harita ve görseli oluşturma
def create_map(latitude, longitude):
    # Harita merkezi olarak koordinatları kullanıyoruz
    map_center = [latitude, longitude]

    # Folium haritası oluşturuluyor
    mymap = folium.Map(location=map_center, zoom_start=18, control_scale=True)

    # Uydu görüntüsü katmanı eklemek için Esri World Imagery kullanıyoruz
    folium.TileLayer(
        'Esri.WorldImagery',
        attr='Tiles © Esri & contributors'
    ).add_to(mymap)

    # 20 km'lik yarıçapı çizmek için folium.Circle kullanıyoruz
    folium.Circle(
        location=map_center,
        radius=5000,  # 5 km = 5000 metre
        color="blue",
        fill=True,
        fill_color="blue",
        fill_opacity=0.1
    ).add_to(mymap)

    # Haritayı kaydetme
    map_path = os.path.join(os.getcwd(), "harita.html")
    mymap.save(map_path)
    return map_path

if __name__ == "__main__":
    main()
