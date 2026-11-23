from database.parco_DAO import ParcoDAO
from database.escursione_DAO import EscursioneDAO
from database.punto_interesse_DAO import PuntoInteresseDAO

class Model:
    def __init__(self):
        self.escursioni_map = {} # Mappa ID escursione -> oggetti Escursione
        self.punti_interesse_map = {} # Mappa ID punto di interesse -> oggetti PuntoInteresse

        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo = 0


        # Caricamento
        self.load_escursioni()
        self.load_punti_interesse()
        self.load_relazioni()

    @staticmethod
    def load_parchi():
        """ Restituisce tutti i parchi disponibili """
        return ParcoDAO.get_parchi()

    def load_escursioni(self):
        """ Carica tutte le escursioni in un dizionario [id, Escursione]"""
        self.escursioni_map = EscursioneDAO.get_escursioni()

    def load_punti_interesse(self):
        """ Carica tutti i punti di interesse in un dizionario [id, PuntoInteresse]"""
        self.punti_interesse_map = PuntoInteresseDAO.get_punti_interesse()

    def load_relazioni(self):
        """
            Interroga il database per ottenere tutte le relazioni fra escursioni e punti di interesse e salvarle nelle strutture dati
            Collega escursione <-> punti di interesse.
            --> Ogni Escursione ha un set di PuntoInteresse.
            --> Ogni PuntoInteresse ha un set di Escursioni.
        """
        risultato = EscursioneDAO.get_escursioni_punti_interesse()
        for i in risultato:
            self.escursioni_map[i["id_escursione"]].punti_interesse.add(self.punti_interesse_map[i["id_punto_interesse"]])
            self.punti_interesse_map[i["id_punto_interesse"]].escursioni.add(self.escursioni_map[i["id_escursione"]])

    def genera_pacchetto(self, id_parco: str, max_giorni: int = None, max_budget: float = None):
        """
        Calcola il pacchetto di escursioni ottimale per un parco rispettando i vincoli di durata, budget e punti di interesse unici.
        :param id_parco: id del parco
        :param max_giorni: numero massimo di giorni (può essere None --> nessun limite)
        :param max_budget: costo massimo del pacchetto (può essere None --> nessun limite)

        :return: self._pacchetto_ottimo (una lista di oggetti Escursione)
        :return: self._costo (il costo del pacchetto)
        :return: self._valore_ottimo (il voto complessivo dei visitatori per il pacchetto)
        """


        codici_escursioni = []
        for i in self.escursioni_map:
            if self.escursioni_map[i].id_parco == id_parco:
                codici_escursioni.append(i)

        risultati =[]
        r = self._ricorsione(codici_escursioni, 0, [], 0,  0, set(), risultati, max_giorni, max_budget)

        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo = 0

        for i in r:
            costo = 0
            voto = 0
            for j in i:
                costo += j.costo
                for k in j.punti_interesse:
                    voto += k.voto_visitatori
            if voto > self._valore_ottimo:
                self._pacchetto_ottimo = i
                self._costo = costo
                self._valore_ottimo = voto

        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

    def _ricorsione(self,codici_escursioni:list,  start_index: int, pacchetto_parziale: list, durata_corrente: int, costo_corrente: float, punti_usati: set, risultati, max_giorni: int = None, max_budget: float = None):
        """ Algoritmo di ricorsione che deve trovare il pacchetto che massimizza il voto complessivo dei visitatori"""

        def sequenza_valida(durata, costo, lista, elemento, insieme_generale, insieme_particolare):
            esito = True
            if max_giorni is not None and durata > max_giorni:
                esito = False
            if max_budget is not None and costo > max_budget:
                esito = False
            if elemento in lista:
                esito = False
            if len(insieme_generale.intersection(insieme_particolare)) > 0:
                esito = False
            return esito

        for i in range(start_index, len(codici_escursioni)):
            durata_corrente += self.escursioni_map[codici_escursioni[i]].durata_giorni
            costo_corrente += self.escursioni_map[codici_escursioni[i]].costo
            punti_interesse =  self.escursioni_map[codici_escursioni[i]].punti_interesse
            if sequenza_valida(durata_corrente, costo_corrente, pacchetto_parziale, codici_escursioni[i], punti_usati, punti_interesse ):
                for j in punti_interesse:
                    punti_usati.add(j)
                pacchetto_parziale.append(self.escursioni_map[codici_escursioni[i]])
                self._ricorsione(codici_escursioni, i+1, pacchetto_parziale, durata_corrente, costo_corrente, punti_usati, risultati, max_giorni, max_budget)
                risultati.append(pacchetto_parziale.copy())
                for j in punti_interesse:
                    punti_usati.discard(j)
                pacchetto_parziale.pop()
            durata_corrente -= self.escursioni_map[codici_escursioni[i]].durata_giorni
            costo_corrente -= self.escursioni_map[codici_escursioni[i]].costo

        return risultati
