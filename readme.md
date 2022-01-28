
# Nive User Database
This package provides the user database for nive applications 'nive_cms' and 'nive_datastore'.
It can be used as standalone user management plugin for pyramid applications though
the installation is not explicitly dcumented. Please refer to 'Nive cms'. 

## Version
The package will soon be released as stable 1.0 version. For a better package management the previous
`nive` package has been split up into several smaller packages.

If you are updating from version 0.9.11 or older please read `update-0.9.11-to-1.0.txt`.
Version 0.9.12 is compatible.

## Source code
The source code is hosted on github: https://github.com/nive/nive_userdb

## Documentation, part of Nive cms
http://cms.nive.co/doc/html/index.html


### Translations
Translations can be extracted using lingua>=3.2

    > pip install lingua-3.2
    > bin/pot-create -o nive_userdb/locale/nive_userdb.pot nive_userdb


# Email tests
Use loacel email test smtp server

    > python -m smtpd -n -c DebuggingServer localhost:1025