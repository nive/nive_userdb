#!/usr/bin/env bash
domain="nive_userdb"
scrp=../nivetest3.7/bin/pot-create

$scrp -o $domain/locale/$domain.pot $domain
