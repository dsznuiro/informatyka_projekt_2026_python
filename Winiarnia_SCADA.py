from multiprocessing import parent_process
import sys
import random
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QSlider, QDialog, QGridLayout, QLabel
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QPainterPath

#Klasa definujaca zbiornik
class Zbiornik:
    def __init__(self, x, y, nazwa, width = 100, height = 140, temp = 20.0, alkohol= 0.0, kolor = QColor(0, 120, 225, 200)):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.nazwa = nazwa
        self.temperatura = temp
        self.alkohol = alkohol
        self.kolor = kolor
        self.pojemnosc = 100.0
        self.aktualna_ilosc = 0.0
        self.poziom = 0.0


    def aktualizuj_poziom(self):
        self.poziom = self.aktualna_ilosc / self.pojemnosc #Wzor na obliczanie poziomu

        #Resetowanie wartosci przy braku cieczy, w celu unikniecia przypadku w ktorym zbiornik nie ma plynu a ma narzucone jakies wartosci
        if self.aktualna_ilosc < 0.1:
            self.aktualna_ilosc = 0.0
            self.temperatura = 20.0
            self.alkohol = 0.0

    def dodaj_ciecz(self, ilosc, temp_dolewana, alk_dolewany, kolor_dolewany):
        #Obliczanie ile plynu ma byc dolanego do zbiornika (zabezpieczenie przed przelaniem)
        wolne = self.pojemnosc - self.aktualna_ilosc
        dodano = min(ilosc,wolne)

        if dodano > 0:
            suma = self.aktualna_ilosc + dodano
            #Obliczanie temperatury cieczy po dolaniu
            self.temperatura = (self.aktualna_ilosc * self.temperatura + dodano * temp_dolewana) / suma

            #Obliczanie stezenia alkoholu po dolaniu
            self.alkohol = (self.aktualna_ilosc * self.alkohol + dodano * alk_dolewany) / suma

            waga_stara = self.aktualna_ilosc / suma
            waga_nowa = dodano / suma

            #Tworzenie stale zmieniajacego sie koloru cieczy na podstawie kolorow dwoch cieczy
            nowy_r = int(self.kolor.red() * waga_stara + kolor_dolewany.red() * waga_nowa)
            nowy_g = int(self.kolor.green() * waga_stara + kolor_dolewany.green() * waga_nowa)
            nowy_b = int(self.kolor.blue() * waga_stara + kolor_dolewany.blue() * waga_nowa)
            
            self.kolor = QColor(nowy_r, nowy_g, nowy_b, 200) #Nowy kolor
        self.aktualna_ilosc += dodano
        self.aktualizuj_poziom()

    #Punkty wykorzystywane do odpowiedniego ulozenia rur
    def punkt_gora_srodek(self):
        return (self.x + self.width / 2, self.y)

    def punkt_dol_srodek(self):
        return (self.x + self.width / 2, self.y + self.height)

    def lewo_srodek(self):
        return (self.x, self.y + self.height / 2)

    def prawo_srodek(self):
        return (self.x + self.width, self.y + self.height / 2)


    def draw(self, painter):
        #Rysowanie cieczy
        if self.poziom > 0:
            h_cieczy = self.height * self.poziom
            y_start = self.y + self.height - h_cieczy
            painter.setPen(Qt.NoPen)
            painter.setBrush(self.kolor)
            painter.drawRect(
                int(self.x + 3),
                int(y_start),
                int(self.width - 6),
                int(h_cieczy - 2)
                )
        #Rysowanie obramowki
        pen = QPen(Qt.white, 4)
        pen.setJoinStyle(Qt.MiterJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(
            int(self.x),
            int(self.y),
            int(self.width),
            int(self.height)
            )
        #Rysowanie tekstu
        painter.setPen(Qt.white)
        painter.drawText(int(self.x), int(self.y - 10), self.nazwa)

#Klasa definiujaca rure
class Rura:
    def __init__(self, punkty, grubosc = 12, kolor_rury=Qt.gray):
        self.punkty = [QPointF(float(p[0]), float(p[1])) for p in punkty]
        self.grubosc = grubosc
        self.kolor_rury = kolor_rury
        self.kolor_cieczy = QColor(Qt.transparent)
        self.czy_plynie = False

    #Ustawienie flagi dotyczaczej przeplywu cieczy w zbioniku
    def ustaw_przeplyw(self,plynie):
         self.czy_plynie = plynie

    def draw(self, painter):
        #Sprawdza czy rura zawiera przynajmniej dwa punkty
        if len(self.punkty) < 2:
            return

        #Wyznaczanie sciezki po okreslonych wczesniej punktach
        path = QPainterPath()
        path.moveTo(self.punkty[0])
        for p in self.punkty[1:]:
            path.lineTo(p)

        #Rysowanie rury
        pen_rura = QPen(self.kolor_rury, self.grubosc, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen_rura)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        #Rysowanie cieczy w rurze (jesli plynie)
        if self.czy_plynie:
            pen_ciecz = QPen(self.kolor_cieczy, self.grubosc - 4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen_ciecz)
            painter.drawPath(path)


class GlowneOkno(QWidget):
    def __init__(self):
        super().__init__()

        #Tworzenie okna
        self.setWindowTitle('Winiarnia') #Tutul okna
        self.setFixedSize(1000, 850) #Wielkosc okna
        self.setStyleSheet("background-color: #616060;") #Kolor tla

        #Tworzenie zbiornikow z roznymi cieczami
        self.z_syrop = Zbiornik(650, 100, "Syrop", temp = 35.0, kolor = QColor(255,0,0))
        self.z_spirytus = Zbiornik(80, 100, "Spirytus", temp = 5.0, alkohol = 96, kolor = QColor(220, 220, 255))
        self.z_cwoda = Zbiornik(300, 100, "Ciepla woda", temp = 45.0, kolor = QColor(255, 150, 150))
        self.z_zwoda = Zbiornik(450, 100, "Zimna woda", temp = 3.0, kolor = QColor(100, 200, 255))

        #Tworzenie mieszalnikow
        self.z_mieszalnik1 = Zbiornik(350, 350, "mieszalnik nr 1", width=300)
        self.z_mieszalnik2 = Zbiornik(50, 450, "mieszalnik nr 2", width=180, height=180)

        #Lista zbiornikow
        self.lista_zbiornikow = [
            self.z_syrop, self.z_spirytus, self.z_zwoda, self.z_cwoda, self.z_mieszalnik2, self.z_mieszalnik1
        ]

        #Rura: pojemnik z spirytusem -> mieszalnik nr 2
        koniec_s_m2 = self.z_mieszalnik2.punkt_gora_srodek()
        start_s_m2 = (koniec_s_m2[0], self.z_spirytus.punkt_dol_srodek()[1])
        self.rura_spirytus = Rura([start_s_m2, koniec_s_m2])

        #Rura: pojemnik z syropem -> mieszalnik nr 1
        start_sy_m1 = self.z_syrop.punkt_dol_srodek()
        koniec_sy_m1 = self.z_mieszalnik1.punkt_gora_srodek()

        przesuniety_koniec_sy_m1 = (koniec_sy_m1[0] + 80, koniec_sy_m1[1])

        #Kolanka w rurze
        kolanko1_sy_m1 = (start_sy_m1[0], start_sy_m1[1] + 35)
        kolanko2_sy_m1 = (koniec_sy_m1[0] + 80, kolanko1_sy_m1[1])

        self.rura_syrop = Rura([start_sy_m1, kolanko1_sy_m1, kolanko2_sy_m1, przesuniety_koniec_sy_m1])

        #Rury z ciepla woda oraz zimna
        koniec_cw_zw_m1 = self.z_mieszalnik1.punkt_gora_srodek()
        p_trojnik = (koniec_cw_zw_m1[0], koniec_cw_zw_m1[1] - 60) #Punkt trojnika

        #Rura: ciepla woda -> trojnik
        start_cw = self.z_cwoda.punkt_dol_srodek()
        self.rura_cw = Rura([start_cw, (start_cw[0], p_trojnik[1]), p_trojnik])

        #Rura: zimna woda -> trojnik
        start_zw = self.z_zwoda.punkt_dol_srodek()
        self.rura_zw = Rura([start_zw, (start_zw[0], p_trojnik[1]), p_trojnik])

        #Wspolna rura dla cieplej i zimnej wody
        self.rura_laczeniowa = Rura([p_trojnik, koniec_cw_zw_m1])

        #Rura: mieszalnik nr 1 -> mieszalnik nr 2
        start_m2_m1 = self.z_mieszalnik2.prawo_srodek()
        koniec_m2_m1 = self.z_mieszalnik1.lewo_srodek()
        kolanko1_m2_m1 = (start_m2_m1[0] + 60, start_m2_m1[1])
        kolanko2_m2_m1 = (kolanko1_m2_m1[0],koniec_m2_m1[1])

        self.rura_mieszalniki = Rura([start_m2_m1, kolanko1_m2_m1, kolanko2_m2_m1, koniec_m2_m1])

        #Rura: mieszalnik nr 2 -> oproznienie
        self.y_podloga = 850
        koniec_m2 = self.z_mieszalnik2.punkt_dol_srodek()
        start_oprozniacz_ukryty = (koniec_m2[0], self.y_podloga)
        koniec_oprozniacz_ukryty = (koniec_m2[0], self.y_podloga + 50)

        self.rura_odbiorcza = Rura([start_oprozniacz_ukryty, koniec_oprozniacz_ukryty])
        
        self.czy_trwa_odbior = False
        self.animacja_pionowa = 0.0
        
        #Kolory poszczegolnych cieczy
        self.rura_spirytus.kolor_cieczy = QColor(220, 220, 255, 180)
        self.rura_syrop.kolor_cieczy = QColor(255, 0, 0, 180)
        self.rura_cw.kolor_cieczy = QColor(255, 150, 150, 180)
        self.rura_zw.kolor_cieczy = QColor(100, 200, 255, 180)
        self.rura_laczeniowa.kolor_cieczy = QColor(200, 200, 255, 150)


        self.lista_rur = [self.rura_spirytus, self.rura_syrop, self.rura_cw, self.rura_zw, self.rura_laczeniowa, self.rura_mieszalniki, self.rura_odbiorcza]

        #Bazowe wypelnienie cieczy
        self.z_syrop.aktualna_ilosc = 80.0
        self.z_spirytus.aktualna_ilosc = 90.0
        self.z_cwoda.aktualna_ilosc = 100.0
        self.z_zwoda.aktualna_ilosc = 100.0

        for z in self.lista_zbiornikow:
            z.aktualizuj_poziom() #Ustawia wszystkie poziomy cieczy na podane wyzej

        #Zegar symulacji aktualizujacy sie co 100ms
        self.timer = QTimer()
        self.timer.timeout.connect(self.fizyka_zbiornika)
        self.timer.start(100)

        #Tworzenie przyciskow

        #Statystyki
        self.btn_stats = QPushButton("STATYSTYKI", self)
        self.btn_stats.setGeometry(820, 200, 150, 40)
        self.btn_stats.setStyleSheet("background-color: #2c3e50; color: white; font-weight: bold;")
        self.btn_stats.clicked.connect(self.pokaz_statystyki)

        #Start/stop
        self.btn_start = QPushButton("START / STOP", self)
        self.btn_start.setGeometry(820, 250, 150, 40)
        self.btn_start.setStyleSheet("background-color: #2c3e50; color: white; font-weight: bold;")
        self.btn_start.clicked.connect(self.przelacz_symulacje)

        #Uzupelnij zbiorniki
        self.btn_refill = QPushButton("Uzupelnij zbiorniki", self)
        self.btn_refill.setGeometry(820, 500, 150, 40)
        self.btn_refill.setStyleSheet("background-color: #2c3e50; color: white; font-weight: bold;")
        self.btn_refill.clicked.connect(self.uzupelnij_zapasy)

        #Tworzenie suwakow

        #Suwak alkoholu
        self.label_alk = QLabel("Docelowy alkohol: 15%", self)
        self.label_alk.setGeometry(820, 360, 150, 20)
        self.label_alk.setStyleSheet("color: white;")

        self.slider_alk = QSlider(Qt.Horizontal, self)
        self.slider_alk.setRange(5, 35)
        self.slider_alk.setValue(15)
        self.slider_alk.setGeometry(820, 385, 150, 30)
        self.slider_alk.valueChanged.connect(self.zmien_poziom_alkohol)

        #Suwak temperatury
        self.label_temp = QLabel("Docelowa temp: 20 C", self)
        self.label_temp.setGeometry(820, 430, 150, 20)
        self.label_temp.setStyleSheet("color: white;")

        self.slider_temp = QSlider(Qt.Horizontal, self)
        self.slider_temp.setRange(13, 35)
        self.slider_temp.setValue(20)
        self.slider_temp.setGeometry(820, 455, 150, 30)
        self.slider_temp.valueChanged.connect(self.zmien_poziom_temp)

        self.czy_m_syrop_gotowy = False
        self.running = False

    #Aktualizacja wyswietlanych wartosci na suwakach

    def zmien_poziom_alkohol(self, value):
        self.label_alk.setText(f"Docelowy alkohol: {value}%")

    def zmien_poziom_temp(self, value):
        self.label_temp.setText(f"Docelowa temp: {value} C")

    #Dzialanie przycisku start/stop
    def przelacz_symulacje(self):
        if self.running:
            self.timer.stop()
            self.btn_start.setText("START")
        else:
            self.timer.start(100)
            self.btn_start.setText("STOP")
        
        self.running = not self.running #Zmiana stanu

    #Uzupelnianie plynow
    def uzupelnij_zapasy(self):
        zapasy = [self.z_syrop, self.z_spirytus, self.z_cwoda, self.z_zwoda]
        
        for z in zapasy:
            z.aktualna_ilosc = 100.0
            
            #Wartosci temperatur oraz alkoholu sa pseudolosowe dla podanych zakresow
            if z == self.z_syrop:
                z.temperatura = random.uniform(30.0, 40.0)
            elif z == self.z_cwoda:
                z.temperatura = random.uniform(40.0, 55.0)
            elif z == self.z_zwoda:
                z.temperatura = random.uniform(1.0, 8.0)
            elif z == self.z_spirytus:
                z.temperatura = random.uniform(5.0, 15.0)
                z.alkohol = random.uniform(92.0, 98.0)

        
        for z in self.lista_zbiornikow:
            z.aktualizuj_poziom()
            
        self.update()

    #Proces automatycznego uzupelniania zbiornika nr 1 (20L syropu, 70L calkowitej ilosci + wybrana temperatura)
    def logika_przeplywu_m1(self):
        docelowy_temp = self.slider_temp.value()
        docelowy_poz = 70.0

        m_syrop = self.z_mieszalnik1

        #Zamyka rury po skonczeniu nalewania
        if self.czy_m_syrop_gotowy:
            self.rura_syrop.czy_plynie = False
            self.rura_cw.czy_plynie = False
            self.rura_zw.czy_plynie = False
            return

        #Nalewa 20L syropu
        if m_syrop.aktualna_ilosc <= 20:
            self.rura_syrop.czy_plynie = True
            self.rura_cw.czy_plynie = False
            self.rura_zw.czy_plynie = False
            return

        #Zamkniecie rury z syropem i rozpoczecie regulacji temperatury
        if m_syrop.aktualna_ilosc < docelowy_poz:
            self.rura_syrop.czy_plynie = False
            
            #Dozowanie odpowiednio cieplej lub zimnej wody
            if m_syrop.temperatura < docelowy_temp:
                self.rura_cw.czy_plynie = True
                self.rura_zw.czy_plynie = False
            else:
                self.rura_cw.czy_plynie = False
                self.rura_zw.czy_plynie = True
        else:
            #Zamkniecie wszystkich rur jesli ilosc soku bedzie wieksza od 70L oraz ustawienie flagi
            self.rura_cw.czy_plynie = False
            self.rura_zw.czy_plynie = False
            self.rura_syrop.czy_plynie = False
            self.czy_m_syrop_gotowy = True
    
    def logika_przeplywu_m2(self):
            m_gora = self.z_mieszalnik1
            m_dol = self.z_mieszalnik2
            docelowy_alk = self.slider_alk.value()
            
            #Warunki plyniecia rury mieszalnik 1 -> mieszalnik 2
            if self.czy_m_syrop_gotowy:
                if m_gora.aktualna_ilosc > 0:
                    self.rura_mieszalniki.czy_plynie = True
                else:
                    self.rura_mieszalniki.czy_plynie = False

                wolne_miejsce = m_dol.aktualna_ilosc < m_dol.pojemnosc

                #Warunki plyniecia rury spirytus -> mieszalnik 2
                if m_dol.aktualna_ilosc > 5 and m_dol.alkohol < docelowy_alk and wolne_miejsce:
                    self.rura_spirytus.czy_plynie = True
                else:
                    self.rura_spirytus.czy_plynie = False



    def fizyka_zbiornika(self):
        if self.running:
            self.logika_przeplywu_m1()
            self.logika_przeplywu_m2()

            #Aktualizacja koloru rury mieszalnik 1 -> mieszalnik 2
            self.rura_mieszalniki.kolor_cieczy = self.z_mieszalnik1.kolor
            
            #Parametry do definiowania momentu oprozniania mieszalnika 2
            cel_alk = self.slider_alk.value()
            m_koncowy = self.z_mieszalnik2
            cel_y_zbiornika = m_koncowy.punkt_dol_srodek()[1]

            #Dzialanie rury z trojnikiem ciepla woda + zimna woda -> mieszalnik 1
            if self.rura_cw.czy_plynie or self.rura_zw.czy_plynie:
                self.rura_laczeniowa.czy_plynie = True
                
                if self.rura_cw.czy_plynie:
                    self.rura_laczeniowa.kolor_cieczy = self.rura_cw.kolor_cieczy
                else:
                    self.rura_laczeniowa.kolor_cieczy = self.rura_zw.kolor_cieczy
            else:
                self.rura_laczeniowa.czy_plynie = False

            if m_koncowy.aktualna_ilosc >= 71 and m_koncowy.alkohol >= cel_alk - 0.5:
                self.czy_trwa_odbior = True #Oznajmia ze mieszalnik 2 powinien byc oprozniony

            if self.czy_trwa_odbior:
                aktualny_y_rury = self.y_podloga - self.animacja_pionowa
                
                if aktualny_y_rury > cel_y_zbiornika:
                    self.animacja_pionowa += 5.0 #Wysuwanie sie rury
                else:
                    if m_koncowy.aktualna_ilosc > 0:
                        #Oproznanie mieszalnika 2 z cieczy
                        self.rura_odbiorcza.czy_plynie = True
                        self.rura_odbiorcza.kolor_cieczy = m_koncowy.kolor
                        m_koncowy.aktualna_ilosc -= 1.0
                    else:
                        #Zamkniecie sie rury
                        self.rura_odbiorcza.czy_plynie = False
                        self.czy_trwa_odbior = False
            else:
                if self.animacja_pionowa > 0:
                    self.animacja_pionowa -= 5.0 #Chowanie sie rury
                else:
                    if m_koncowy.aktualna_ilosc <= 0 and self.z_mieszalnik1.aktualna_ilosc <= 0:
                        #Resetowanie zbiornika (mieszalnik nr 2)
                        self.czy_m_syrop_gotowy = False
                        m_koncowy.kolor = QColor(0, 120, 225, 200)
                        self.z_mieszalnik1.kolor = QColor(0, 120, 225, 200)

        predkosc = 0.5 #Wartosc predkosci przeplywu cieczy

        #Przeplyw plynow w oparciu o flagi rur
        #Zbiornik z syropem -> mieszalnik nr 1
        if self.rura_syrop.czy_plynie and self.z_syrop.aktualna_ilosc > 0:
            self.z_syrop.aktualna_ilosc -= predkosc
            self.z_mieszalnik1.dodaj_ciecz(predkosc, self.z_syrop.temperatura, self.z_syrop.alkohol, self.z_syrop.kolor)

        #Zbiorik z ciepla woda -> mieszalnik nr 1
        if self.rura_cw.czy_plynie and self.z_cwoda.aktualna_ilosc > 0:
            self.z_cwoda.aktualna_ilosc -= predkosc
            self.z_mieszalnik1.dodaj_ciecz(predkosc, self.z_cwoda.temperatura, self.z_cwoda.alkohol, self.z_cwoda.kolor)

        #Zbiornik z zimna woda -> mieszalnik nr 1
        if self.rura_zw.czy_plynie and self.z_zwoda.aktualna_ilosc > 0:
            self.z_zwoda.aktualna_ilosc -= predkosc
            self.z_mieszalnik1.dodaj_ciecz(predkosc, self.z_zwoda.temperatura, self.z_zwoda.alkohol, self.z_zwoda.kolor)

        #Zbiornik ze spirytusem -> mieszalnik nr 2
        if self.rura_spirytus.czy_plynie and self.z_spirytus.aktualna_ilosc > 0:
            self.z_spirytus.aktualna_ilosc -= predkosc
            self.z_mieszalnik2.dodaj_ciecz(predkosc, self.z_spirytus.temperatura, self.z_spirytus.alkohol, self.z_spirytus.kolor)

        #Mieszalnik nr 1 -> mieszalnik nr 2
        if self.rura_mieszalniki.czy_plynie and self.z_mieszalnik1.aktualna_ilosc > 0:
            self.z_mieszalnik1.aktualna_ilosc -= predkosc
            self.z_mieszalnik2.dodaj_ciecz(predkosc, self.z_mieszalnik1.temperatura, self.z_mieszalnik1.alkohol, self.z_mieszalnik1.kolor)

        for z in self.lista_zbiornikow:
            z.aktualizuj_poziom()

        self.update()

    def pokaz_statystyki(self):
        self.okno = OknoStatystyk(self)
        self.okno.show()


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        #Rysowanie rur
        for rura in self.lista_rur:
            if rura == self.rura_odbiorcza:
                p0_start = rura.punkty[0]
                p1_start = rura.punkty[1]

                #Przeniesienie rury do gory/dolu
                rura.punkty[0] = QPointF(p0_start.x(), self.y_podloga - self.animacja_pionowa)
                rura.punkty[1] = QPointF(p1_start.x(), self.y_podloga + 50)
                
                rura.draw(painter)
                
                #Przywrocenie punktow startowych
                rura.punkty[0] = p0_start
                rura.punkty[1] = p1_start
            else:
                rura.draw(painter)
        #Rysowanie zbiornikow
        for zbiornik in self.lista_zbiornikow:
            zbiornik.draw(painter)

#Dodatkowe okno z danymi cieczy
class OknoStatystyk(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.setWindowTitle("Statystyki Zbiornikow")
        self.setFixedSize(400, 300)

        self.layout = QGridLayout(self) #Uklad tabelaryczny

        #Naglowki tabeli
        self.layout.addWidget(QLabel("Zbiornik"), 0, 0)
        self.layout.addWidget(QLabel("Temp"), 0, 1)
        self.layout.addWidget(QLabel("Alkohol"), 0, 2)
        self.layout.addWidget(QLabel("Ilosc"), 0, 3)

        self.etykiety = [] 

        row = 1
        #Tworzenie wierszy dla kazdego zbiornika
        for zbiornik in self.parent.lista_zbiornikow:
            nazwa = QLabel()
            temp = QLabel()
            alkohol = QLabel()
            ilosc = QLabel()

            #Ustawienie odpowiednich danych w odpowiednich miejscach
            self.layout.addWidget(nazwa, row, 0)
            self.layout.addWidget(temp, row, 1)
            self.layout.addWidget(alkohol, row, 2)
            self.layout.addWidget(ilosc, row, 3)

            #Zapisane etykiet
            self.etykiety.append((nazwa, temp, alkohol, ilosc))
            row += 1

        #Odswiezanie danych w tabeli co 500ms
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.odswiez_dane)
        self.timer.start(500)

        self.odswiez_dane()

    def odswiez_dane(self):
        for i in range(len(self.parent.lista_zbiornikow)):
            #Ustawianie odpowiednich wartosci dla tabeli
            nazwa, temp, alkohol, ilosc = self.etykiety[i]

            nazwa.setText(self.parent.lista_zbiornikow[i].nazwa)
            temp.setText(f"{self.parent.lista_zbiornikow[i].temperatura:.1f} C")
            alkohol.setText(f"{self.parent.lista_zbiornikow[i].alkohol:.1f} %")
            ilosc.setText(f"{self.parent.lista_zbiornikow[i].aktualna_ilosc:.1f} L")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    okno = GlowneOkno()
    okno.show()
    sys.exit(app.exec_())
