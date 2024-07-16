
# Nive User Database
This package provides the user database for nive applications based on 'nive'.
It can be used as standalone user management plugin for pyramid applications though
the installation is not explicitly dcumented.

## Source code
The source code is hosted on github: https://github.com/nive/nive_userdb

### Translations
Translations can be extracted using lingua>=3.2

    > pip install lingua-3.2
    > bin/pot-create -o nive_userdb/locale/nive_userdb.pot nive_userdb


# Email tests
Use loacel email test smtp server

    > python -m smtpd -n -c DebuggingServer localhost:1025
    
    
