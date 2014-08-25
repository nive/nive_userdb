
# Nive User Database
This package provides the user database for nive applications 'nive_cms' and 'nive_datastore'.
It can be used as standalone user management plugin for pyramid applications though
the installation is not explicitly dcumented. Please refer to 'Nive cms'. 

## Version
This version is a beta release. The application is stable and complete. The public API as documented 
on the website is stable will not change. 

## Source code
The source code is hosted on github: https://github.com/nive/nive_userdb

## Documentation, part of Nive cms
http://cms.nive.co/doc/html/index.html


### Translations
Translations can be extracted using lingua>=3.1

    > pip install lingua-3.1
    > bin/pot-create -o nive_userdb/locale/nive_userdb.pot nive_userdb
