# wg-ha

```
sudo nix-shell --run "python3 main.py"
```


```
*/5 * * * * python3 /home/pi/test.py >> /home/pi/cron_out.txt
0 */2 * * * rm -f /home/pi/cron_out.txt
```