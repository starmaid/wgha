
```
*/5 * * * * python3 /home/pi/test.py >> /home/pi/cron_out.txt
0 */2 * * * rm -f /home/pi/cron_out.txt
```