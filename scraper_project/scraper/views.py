from django.shortcuts import render

# Create your views here.
import time
from django.shortcuts import render
from .models import JobOffer
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options

def job_search(request):
    if request.method == 'POST':
        search_term = request.POST.get('search_term')
        if search_term:
            options = Options()
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-extensions")

            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            options.add_argument(f"user-agent={user_agent}")

            driver = uc.Chrome(options=options)
            driver.get("https://www.infojobs.net/")
            time.sleep(4)

            try:
                submit_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "didomi-notice-agree-button"))
                )
                submit_button.click()
            except Exception as e:
                print(f"Error: {e} - Agree button not found or already clicked.")

            try:
                search_box = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "palabra"))
                )
                search_box.send_keys(search_term)

                search_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "searchOffers"))
                )
                search_button.click()
                time.sleep(4)

                previous_count = 0
                while True:
                    offers = driver.find_elements(By.CSS_SELECTOR, "div.sui-AtomCard")
                    total_offers = len(offers)

                    if total_offers == previous_count:
                        break
                    previous_count = total_offers

                    driver.execute_script("arguments[0].scrollIntoView();", offers[-1])
                    time.sleep(2)

                for offer in offers:
                    try:
                        title = offer.find_element(By.CSS_SELECTOR, "h2.ij-OfferCardContent-description-title a").text
                        company_element = offer.find_element(By.CSS_SELECTOR, "h3.ij-OfferCardContent-description-subtitle a")
                        company = company_element.text
                        company_url = company_element.get_attribute("href")
                        location = offer.find_element(By.CSS_SELECTOR, "li.ij-OfferCardContent-description-list-item").text
                        
                        # Validación para el salario
                        try:
                            salary = offer.find_element(By.CSS_SELECTOR, ".ij-OfferCardContent-description-salary-info").text
                        except:
                            salary = "No disponible"  # Si no se encuentra el salario, asignamos "No disponible"

                        work_mode = offer.find_elements(By.CSS_SELECTOR, ".ij-OfferCardContent-description-list-item")[1].text
                        contract_type = offer.find_element(By.CSS_SELECTOR, ".ij-OfferCardContent-description-list-item--hideOnMobile").text
                        workday = offer.find_elements(By.CSS_SELECTOR, ".ij-OfferCardContent-description-list-item--hideOnMobile")[1].text

                        # Guardamos la oferta en la base de datos
                        JobOffer.objects.create(
                            title=title,
                            company=company,
                            company_url=company_url,
                            location=location,
                            salary=salary,
                            work_mode=work_mode,
                            contract_type=contract_type,
                            workday=workday
                        )
                    except Exception as e:
                        print(f"Error scraping offer: {e}")

                driver.quit()
                return render(request, 'scraper/results.html', {'message': 'Search completed!'})
            except Exception as e:
                driver.quit()
                return render(request, 'scraper/results.html', {'error': f"Error: {e}"})
    return render(request, 'scraper/search.html')
