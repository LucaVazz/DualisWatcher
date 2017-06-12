# Dualis: Structural Documentation

> Well, yeah... Dualis was definitively not meant to be used this way, but do I really give the impression that I care about that at all?

This document is very hacky and the contained assumptions are prone to break at any time.


### General Behaviour
**base URL:** `https://dualis.dhbw.de/scripts`

**basic Headers:** `Cookie`: `cnsc=0`


### General Error Messages:
- HTTP-Status Code 200
- page with both
    - a `<form id="cn_loginForm">` 
    - a`<div id="pageContent">` containing a `<h1>` and a following `<p>` which combined contain the description of the error
        - They may contain additional elements like `&nbsp;`, `<b>`, `</b>`, `<br />`


### POSTing the Login
**Endpoint**: `/mgrqcgi`

**Request-Payload:** URL-Encoded Form with:
- `usrname`
- `pass`
- `ARGUMENTS`: `clino,usrname,pass,menuno,menu_type,browser,platform`
- `APPNAME`: `CampusNet`
- `PRGNAME`: `LOGINCHECK`

**Response:** HTTP-Status Code 200, page with empty body and the relevant Header field *REFRESH*: `0; URL=/scripts/mgrqcgi?APPNAME=CampusNet&PRGNAME=STARTPAGE_DISPATCH&ARGUMENTS=-N<token>,-N000019,-N000000000000000`


### GETting the List of Result-Lists
**Endpoint:** `/mgrqcgi?APPNAME=CampusNet&PRGNAME=COURSERESULTS&ARGUMENTS=-N<token>,-N000307,`

**Response**: page with a `<select id="semester">` containing several options like `<option value="<semesterId>" ><courseName></option>`


### GETting One Result-List
**Endpoint:** `/mgrqcgi?APPNAME=CampusNet&PRGNAME=COURSERESULTS&ARGUMENTS=-N<token>,-N000307,-N<semesterId>`

**Response:** page with a `<table class="nb list">` containing several links like `<a id="Popup_details0001" href="/scripts/mgrqcgi?APPNAME=CampusNet&amp;PRGNAME=RESULTDETAILS&amp;ARGUMENTS=-<token>,-N000307,-N<courseId>,-N000000015024000">Prüfungen</a>`


### GETting One Course-Result
**Endpoint**: `/mgrqcgi?APPNAME=CampusNet&PRGNAME=RESULTDETAILS&ARGUMENTS=-N<token>,-N000307,-N<courseId>`

**Response**: page with the following:
- a `<h1>` containing the full course title
- the first `<table class="tb">` containing the exams and grades associated with the course
- the second and possibly third `<table class="tb">` which contain the mandatory and selectable lectures for the course
