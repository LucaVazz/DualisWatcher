# DualisWatcher

> Because refreshing the same page manually every few days is just ~~way too easy~~ inefficient.


### Disclaimer
*This software is not affiliated, associated, authorized, endorsed by, or in any way officially connected with Duale Hochschule Baden-Württemberg or Datenlotsen Informationssysteme GmbH or any of its subsidiaries or its affiliates.*    
*This software is provided "as is" and any expressed or implied warranties, including, but not limited to, the implied warranties of merchantability and fitness for a particular purpose are disclaimed. In no event shall the author or additional contributors be liable for any direct, indirect, incidental, special, exemplary, or consequential damages (including, but not limited to, procurement of substitute goods or services; loss of use, data, or profits; or business interruption).*


### Features
- Watch your Dualis Account for additions, deletions or changes to your course results.
- Optionally also watch a DHBW Mannheim Schedule for changes.
- Optionally get notified via mail about these changes.
- Save yourself precious time through all these nice features.


### Setup
1. Install [git](https://git-scm.com/) >2.12
2. Install [Python](https://www.python.org/) >=3.5.3 `apt-get install python3 && apt-get install python3-pip`
3. Verify that `python --version` shows a version equal to or higher then 3.5.3
    Otherwise use [pyenv](https://github.com/pyenv/pyenv#installation) to install version 3.5.3
4. `pip3 install -r requirements.txt`
5. run `python3 main.py --init`


### Usage
- `python main.py`
    - Fetches the current state of your Dualis Account, saves it and detects any changes.
    - If configured, it also sends out a mail-notification.
    - It doesn't print out any console output, but it writes into `DualisWatcher.log`.
- `python main.py --init`
    - Guides you trough the configuration of the software, including the activation of mail-notifications and obtainment of a login-token for your Dualis-Account.
    - It also fetches the current state of your Dualis-Account. (But it will not check for any changes to a possible previous state.)
    - It prints all information into the console.
- `python main.py --new-token`
    - Overrides the login-token with a newly obtained one.
    - It does not fetch the current state of your Dualis-Account.
    - Use it if at any point in time, for whatever reason, the saved token gets rejected by Dualis.
    - It does not affect the rest of the config.
    - It prints all information into the console.
- `python main.py --change-schedule-watcher`
    - Activate/deactivate/change the watched UID for watching a DHBW Mannheim Schedule for changes.
    - It also fetches the current state as a base if activated/changed.
    - It does not affect the rest of the config.
    - It prints all information into the console.
- `python main.py --change-notification-mail`
    - Activate/deactivate/change the settings for receiving notifications via e-mail.
    - It does not affect the rest of the config.
    - It prints all information into the console.


### Notes
- Use a separate E-Mail - Account for sending out the notifications, as its login data is saved in cleartext.
- The Login-Information for your Dualis-Account is secure, it isn't saved in any way. Only a Login-Token is saved.


---


### Contributing
I'm open for all forks, feedback and Pull Requests ;)


### License
This project is licensed under the terms of the *GNU General Public License v3.0*. For further information, please look [here](http://choosealicense.com/licenses/gpl-3.0/) or [here<sup>(DE)</sup>](http://www.gnu.org/licenses/gpl-3.0.de.html).
