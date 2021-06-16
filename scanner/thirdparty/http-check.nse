local http = require "http"
local stdnse = require "stdnse"


author = "unknow"

license = "Same as Nmap--See https://nmap.org/book/man-legal.html"

categories = {"discovery"}

portrule = function(host, port)
  return true
end

action = function(host,port)
	local result = http.generic_request(host,port,"OPTIONS","/",nil)
	local http_header = stdnse.output_table()
	http_header.date = result.header["date"]
	return http_header
end

