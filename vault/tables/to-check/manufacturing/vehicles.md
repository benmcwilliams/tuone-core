```dataview
table location, company, tech, component, status, capacity, investment_value, dt_announce
from "src/phases" 
where checked = false and reject-phase = false and tech = "vehicle" and component = "battery_vehicle_assembly"
sort location, company asc
```


