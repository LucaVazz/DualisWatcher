# DualisWatcher

> Because refreshing the same page manually every few days is just to ~easy~ inefficient.

### Disclaimer
*This software is not affiliated, associated, authorized, endorsed by, or in any way officially connected with Duale Hochschule Baden-Württemberg or Datenlotsen Informationssysteme GmbH or any of its subsidiaries or its affiliates.*    
*This software is provided "as is" and any expressed or implied warranties, including, but not limited to, the implied warranties of merchantability and fitness for a particular purpose are disclaimed. In no event shall the author or additional contributors be liable for any direct, indirect, incidental, special, exemplary, or consequential damages (including, but not limited to, procurement of substitute goods or services; loss of use, data, or profits; or business interruption).*

### Setup
1. Install [git](https://git-scm.com/) >2.12
2. Install [Python](https://www.python.org/) >3.6
3. `pip install beautifulsoup4`
4. `pip install pygments`
5. run `python main.py --init`

### Usage
- `python main.py`
    - Fetches the current state of your Dualis Account, saves it and detects any changes.
    - If configured, it also sends out a mail-notification.
    - It doesn't print out any console output, but it writes `DualisWatcher.log`.
- `pythin main.py --init`
    - Guides you trough the configuration of the software, including the activation of mail-notifications and obtainment of a login-token for your Dualis-Account.
    - It prints all information into the console.
- `python main.py --new-token`
    - Overrides the login-token with a newly obtained one.
    - Use it if at any point in time, for whatever reason, the saved token gets rejected by Dualis.
    - Doesn't change any of the other settings (contrary to `--init`).
    - It prints all information into the console.

### Notes
- Use a separate E-Mail - Account for sending out the notifications, as its login data is saved in cleartext.
- The Login-Information for your Dualis-Account is save, it isn't saved in any way. Only a Login-Token is saved.


---


### Contributing
I'm open for all forks, feedback and Pull Requests ;)


### License
This project is licensed under the terms of the *GNU General Public License v3.0*. For further information, please look [here](http://choosealicense.com/licenses/gpl-3.0/) or [here<sup>(DE)</sup>](http://www.gnu.org/licenses/gpl-3.0.de.html).
