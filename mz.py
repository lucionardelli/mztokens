import logging
import sys
import os
import time

from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


HEADLESS = True
WEB_PRINCIPAL = "https://www.managerzone.com/"
WEB_HOME = "https://www.managerzone.com/?p=clubhouse"
WEB_EVENTO = "https://www.managerzone.com/?p=event"

ID_USERNAME_INPUT = 'login_username'
ID_PASSWORD_INPUT = 'login_password'
ID_BUTTON_LOGIN = 'login'
ID_BUTTON_RECLAMAR = 'claim'
ID_BUTTON_CHALLENGE = 'challenge_1'
ID_BUTTON_CHALLENGE_5 = 'challenge_5'
ID_BUTTON_JUGAR = 'get_it_btn'
ID_TACTICS_SELECT = 'tacticSet'
TIMEOUT = 10  # We wait for TIMEOUT seconds waiting for pages to load

AUTOMATIC_PLAY = True
MATCHS_PER_CLAIM = 5
AUTOMATIC_PLAY_U18 = False
USE_TACTIC = None


logging.basicConfig()
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)
log_handler = logging.FileHandler('/tmp/mz.log')
log_handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s]: %(message)s'))
LOG.addHandler(log_handler)

load_dotenv()


def is_button_enabled(button):
    for klass in button.get_attribute('class').split():
        print(f"{klass=}")
    return 'buttondiv_disabled' not in button.get_attribute('class').split()


def wait_for_page_to_load(driver, expected_page, timeout=TIMEOUT):
    while driver.current_url != expected_page and timeout > 0:
        LOG.debug("Esperando que se haga el login...")
        time.sleep(1)
        timeout -= 1
    return driver.current_url == expected_page


def login(driver):
    driver.get(WEB_PRINCIPAL)

    username = os.getenv("MZ_USERNAME")
    password = os.getenv("MZ_PASSWORD")

    if not (username and password):
        LOG.error("Username and/or password are not set. Did you create the `.env` file?")
        driver.close()
        sys.exit(1)

    login_input = WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.ID, ID_USERNAME_INPUT)))
    login_input.clear()
    login_input.send_keys(username)

    password_input = driver.find_element(By.ID, ID_PASSWORD_INPUT)
    password_input.clear()
    password_input.send_keys(password)

    login_button = driver.find_element(By.ID, ID_BUTTON_LOGIN)
    login_button.click()

    wait_for_page_to_load(driver, WEB_HOME)

    # LOG.debug(f"La current url es: {driver.current_url}.")
    if driver.current_url != WEB_HOME:
        return False

    LOG.info("WE'RE IN! Joya, vamos a la página del evento ahora...")
    return True


def go_to_event(driver):
    driver.get(WEB_EVENTO)


def claim_tickets(driver):
    claim_button = WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.ID, ID_BUTTON_RECLAMAR)))
    time.sleep(10)
    if is_button_enabled(claim_button):
        LOG.debug("QUIERO FLAAAAAAAN!")
        claim_button.send_keys(Keys.RETURN)
        LOG.debug("Ya tenés tu plan!")
        return True
    else:
        LOG.debug("No seas ansioso! Todavía no estamos para reclamar nada!")
        return False


def automatically_play_in_event(driver, use_tactic=None, play_5_special=False):
    # We want a bigge wait time for challenging new teams. A previous match could be taking place!
    WAIT_UNTIL_PREVIOUS_MATCH_ENDS = 60
    if play_5_special:
        button_id = ID_BUTTON_CHALLENGE_5
    else:
        button_id = ID_BUTTON_CHALLENGE
    challenge_button = WebDriverWait(driver, WAIT_UNTIL_PREVIOUS_MATCH_ENDS).until(EC.presence_of_element_located((By.ID, button_id)))
    if challenge_button.is_enabled():
        LOG.debug("Salen los equipos a la cancha....")
        challenge_button.click()
        time.sleep(2)
        play_button = WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.ID, ID_BUTTON_JUGAR)))
        if play_button.is_enabled():
            if use_tactic is not None:
                tactics = driver.find_element(By.ID, ID_TACTICS_SELECT)
                # tactics.select_by_visible_text('Banana')
                for option in tactics.find_elements_by_tag_name('option'):
                    if option.text.lower() == use_tactic:
                        option.click() # select() in earlier versions of webdriver
                        break
                else:
                    LOG.debug("Disculpa mostro, pero no sé qué táctica es %s. Vamos a salir con la default...", use_tactic)

            LOG.debug("Ahora juega Booooooca!")
            play_button.click()
        else:
            LOG.debug("No hay fichines para jugar amistosos!")
    else:
        LOG.debug("Algo anduvo mal, no nos dejan jugar!")

if __name__ == '__main__':

    options = webdriver.ChromeOptions()
    if HEADLESS:
        options.add_argument("--headless")
    # NOTE esto es para utilizar el chromedriver que está descargado en .
    # with webdriver.Chrome(executable_path='./chromedriver', chrome_options=chrome_options) as driver:
    # NOTE esto debería instalar el chromedriver automágicamente
    with webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options) as driver:
        LOG.debug("Reclamando tickets usando %s", sys.argv[0])
        succesful_login = False
        try:
            succesful_login = login(driver)
        except Exception as err:
            LOG.error(
                "Algo anduvo MUY mal, lo siento! No nos pudimos conectar! Escribile a magoya con tus reclamos y pasale este ST: %s.", err)
        if not succesful_login:
            LOG.error("Si no nos podemos logear, no podemos hacer nada. Chauuuu")
            driver.close()
            sys.exit(1)

        go_to_event(driver)
        got_tickets = claim_tickets(driver)

        if got_tickets and AUTOMATIC_PLAY:
            use_tactic = AUTOMATIC_PLAY_U18 and 'u18' or USE_TACTIC or None
            if MATCHS_PER_CLAIM % 5 == 0:
                # Play in multiples of 5
                games_to_play = MATCHS_PER_CLAIM
                while games_to_play:
                    LOG.debug("Vamos al mejor de 5 partido' (de un total de %s)", MATCHS_PER_CLAIM)
                    automatically_play_in_event(driver, use_tactic=use_tactic, play_5_special=True)
                    games_to_play -= 5
            else:
                for i in range(MATCHS_PER_CLAIM):
                    automatically_play_in_event(driver, use_tactic=use_tactic)
    LOG.debug("Vuelva prontosss")
