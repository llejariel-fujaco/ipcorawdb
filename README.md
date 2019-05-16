## ipcorawdb

### DB examples
#### Mongo local raw_ip_data query
---------------------------------------------------------------------------------------
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
---------------------------------------------------------------------------------------

```
db.raw_ip_data.find(
	{$or:[	{"status.status":"DONE"},
			{"status.status":"TO_PROCESS"}]
	},
	{	"_id":0,
		"ip_addr":1,
		"aclass":1,
		"geo_data.hostname":1,
		"geo_data.country_name":1,
		"geo_data.region_name":1,
		"geo_data.city":1,
		"rdap_data.network.name":1,
		"rdap_data.network.cidr":1,
		"rdap_data.network.start_address":1,
		"rdap_data.network.end_address":1,
		"geo2_data.country_name":1,
		"geo2_data.state":1,
		"geo2_data.city":1
	}
).map( (doc) => ({
					"ip_addr": doc.ip_addr,
					"aclass":doc.aclass,
					"geo_hostname": doc.geo_data
				}
				)
	);
```
---------------------------------------------------------------------------------------
```
// Companies where company_bvd_num eq hq_bvd_num
db.raw_company_data.find({$where: function() { return this.company_bvd_num == this.hq_bvd_num } } );

// Different hq_types
db.raw_company_data.aggregate([
	{$match: {}},
	{$group:{_id:'$hq_type', count:{$sum:1}}}
]
)

// All HQ 
db.raw_company_data.aggregate([
	{$match: {}},
	{$group:{_id:'$hq_bvd_num', count:{$sum:1}, hq_name: {$first:"$hq_name"}, hq_type: {$first:"$hq_type"}}},
	{$project: {"_id":1, "count":1, "hq_name":1, "hq_type":1}},
	{$sort: { count:-1 }}
]
)
	
// Cursor
var comp_cur=db.raw_company_data.find({hq_bvd_num:'DE*850267597'})
while(comp_cur.hasNext()){ print(tojson(comp_cur.next())); }
```



