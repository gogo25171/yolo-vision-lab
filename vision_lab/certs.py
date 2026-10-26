"""Réseau : certificats système et contournement des antivirus qui inspectent le HTTPS."""

import os
import sys


def use_system_certificates() -> None:
    # Certains antivirus (Avast, AVG…) définissent SSLKEYLOGFILE vers un tube nommé Windows
    # (« \\.\aswMonFltProxy\… »). Avec Python 3.14, OpenSSL tente d'y écrire et plante
    # (« OPENSSL_Uplink: no OPENSSL_Applink ») : on retire la variable pour ce processus.
    keylog = os.environ.get("SSLKEYLOGFILE", "")
    if sys.platform == "win32" and keylog.startswith("\\\\.\\"):
        os.environ.pop("SSLKEYLOGFILE")

    # Derrière un proxy/antivirus qui inspecte le HTTPS, les téléchargements de modèles
    # échouent (CERTIFICATE_VERIFY_FAILED) : truststore utilise le magasin de l'OS.
    try:
        import truststore

        truststore.inject_into_ssl()
    except ImportError:
        pass
