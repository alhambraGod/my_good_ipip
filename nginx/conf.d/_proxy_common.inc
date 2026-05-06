# Common proxy directives — included by every `location ... { proxy_pass ... }` block.
#
# Goals:
#   1. Pass real client info to the backend (X-Real-IP, X-Forwarded-*).
#   2. Use HTTP/1.1 + connection: keep-alive against upstreams (cheaper).
#   3. Sane timeouts: snapshot at 60s. Bump for known-slow Razorpay calls
#      (the FastAPI client already times out at 15s upstream).

proxy_http_version 1.1;
proxy_set_header   Connection         "";
proxy_set_header   Host               $host;
proxy_set_header   X-Real-IP          $remote_addr;
proxy_set_header   X-Forwarded-For    $proxy_add_x_forwarded_for;
proxy_set_header   X-Forwarded-Proto  $scheme;
proxy_set_header   X-Forwarded-Host   $host;
proxy_set_header   Upgrade            $http_upgrade;
proxy_set_header   Connection         $connection_upgrade;

proxy_connect_timeout 5s;
proxy_send_timeout    60s;
proxy_read_timeout    60s;

proxy_buffering on;
proxy_buffer_size 8k;
proxy_buffers 16 8k;
proxy_busy_buffers_size 16k;

# Don't pass through Razorpay error pages verbatim.
proxy_intercept_errors off;

# Per-request retry on a different upstream when the picked one is down.
proxy_next_upstream error timeout http_502 http_503 http_504;
proxy_next_upstream_tries 2;
proxy_next_upstream_timeout 5s;
