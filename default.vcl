vcl 4.0;

backend default {
    .host = "app";
    .port = "8001";
}

# Only cache GET requests, set TTL to "infinite"
sub vcl_recv {
    if (req.method == "POST") {
        return (pass);
    }

    if (req.method == "PURGE") {
        if (client.ip != "127.0.0.1") {
            return (synth(405, "Not allowed."));
        }
        return (purge);
    }

    return (hash);
}

sub vcl_backend_response {
    if (bereq.method == "GET") {
        set beresp.ttl = 365d; # Cache for 1 year (effectively infinite)
    }
}

sub vcl_deliver {
    # Optional: Add cache status headers for debugging
    if (obj.hits > 0) {
        set resp.http.X-Cache = "HIT";
    } else {
        set resp.http.X-Cache = "MISS";
    }
}
