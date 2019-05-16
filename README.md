# ipcorawdb

# DB examples
## ---------------------------------------------------------------------------------------
## Mongo local raw_ip_data query
## ---------------------------------------------------------------------------------------
```mongodb
db.raw_ip_data.aggregate([
	{$match: {$or:[	{"status.status":"DONE"},
					{"status.status":"TO_PROCESS"}]}
	},
	{$project: {"_id":0,
				"ip_addr":1,
				"aclass":1,
				"geo_hostname":"$geo_data.hostname",
				"geo_country":"$geo_data.country_name",
				"geo_region":"$geo_data.region_name",
				"geo_city":"$geo_data.city",
				"geo2_country":"$geo2_data.country_name",
				"geo2_region":"$geo2_data.state",
				"geo2_city":"$geo2_data.city",
				"rdap_netname":"$rdap_data.network.name",
				"rdap_cidr":"$rdap_data.network.cidr",
				"rdap_start_addr":"$rdap_data.network.start_address",
				"rdap_end_addr":"$rdap_data.network.end_address"
				}
	},
	{$sort: { ip_addr: 1}
	},
	{$out: "evelean_ip"
	}
]);
```

