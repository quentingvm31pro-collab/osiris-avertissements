import time
import requests


class APIClientError(Exception):
    pass


class APIClient:
    def __init__(self, base_url="https://osiris-api.onrender.com"):
        self.base_url = base_url.rstrip("/")
        self.token = None

        # Pour les hébergements gratuits qui se réveillent lentement
        self.connect_timeout = 30
        self.read_timeout = 60
        self.max_retries = 3
        self.retry_delay = 3

    def set_token(self, token: str):
        self.token = token

    def _headers(self):
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(self, method: str, endpoint: str, **kwargs):
        url = f"{self.base_url}{endpoint}"

        headers = kwargs.pop("headers", {})
        merged_headers = {**self._headers(), **headers}

        timeout = kwargs.pop("timeout", (self.connect_timeout, self.read_timeout))

        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=merged_headers,
                    timeout=timeout,
                    **kwargs,
                )

                if response.status_code == 401:
                    try:
                        detail = response.json().get("detail", "Accès non autorisé.")
                    except Exception:
                        detail = "Accès non autorisé."
                    raise APIClientError(detail)

                if response.status_code == 404:
                    try:
                        detail = response.json().get("detail", "Ressource introuvable.")
                    except Exception:
                        detail = "Ressource introuvable."
                    raise APIClientError(detail)

                if response.status_code >= 400:
                    try:
                        detail = response.json().get("detail")
                        if detail:
                            raise APIClientError(detail)
                    except ValueError:
                        pass

                    response.raise_for_status()

                return response

            except requests.exceptions.Timeout:
                last_error = APIClientError(
                    "Le serveur met trop de temps à répondre. "
                    "S'il vient de se réveiller, réessaie dans quelques secondes."
                )

            except requests.exceptions.ConnectionError:
                last_error = APIClientError(
                    "Impossible de contacter le serveur. "
                    "Vérifie l'URL de l'API ou attends quelques secondes si l'hébergement gratuit se réveille."
                )

            except requests.exceptions.HTTPError as e:
                last_error = APIClientError(f"Erreur HTTP : {e}")

            except APIClientError as e:
                raise e

            except Exception as e:
                last_error = APIClientError(f"Erreur réseau : {e}")

            if attempt < self.max_retries:
                time.sleep(self.retry_delay)

        raise last_error or APIClientError("Erreur inconnue lors de la requête API.")

    def ping(self):
        response = self._request("GET", "/")
        return response.json()

    def register_officer(self, pseudo: str, email: str, password: str):
        response = self._request(
            "POST",
            "/officers/register",
            params={
                "pseudo": pseudo,
                "email": email,
                "password": password,
            },
        )
        return response.json()

    def login(self, email: str, password: str):
        response = self._request(
            "POST",
            "/officers/login",
            data={
                "username": email,
                "password": password,
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        result = response.json()
        self.token = result["access_token"]
        return result

    def get_players(self):
        response = self._request("GET", "/players")
        return response.json()

    def get_players_with_warnings(self):
        response = self._request("GET", "/players-with-warnings")
        return response.json()

    def create_player(self, name: str):
        response = self._request(
            "POST",
            "/players",
            params={"name": name},
        )
        return response.json()

    def get_warnings(self):
        response = self._request("GET", "/warnings")
        return response.json()

    def get_player_warnings(self, player_id: int):
        response = self._request("GET", f"/players/{player_id}/warnings")
        return response.json()

    def create_warning(self, player_id: int, reason: str, date: str):
        response = self._request(
            "POST",
            "/warnings",
            params={
                "player_id": player_id,
                "reason": reason,
                "date": date,
            },
        )
        return response.json()

    def update_warning(self, warning_id: int, reason: str, date: str):
        response = self._request(
            "PUT",
            f"/warnings/{warning_id}",
            params={
                "reason": reason,
                "date": date,
            },
        )
        return response.json()

    def delete_warning(self, warning_id: int):
        response = self._request("DELETE", f"/warnings/{warning_id}")
        return response.json()

    def delete_player(self, player_id: int):
        response = self._request("DELETE", f"/players/{player_id}")
        return response.json()