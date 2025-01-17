```dataview
table location, company, tech, component, status, capacity, investment_value, dt_announce
from "src/phases" 
where checked = false and reject-phase = false and tech = "solar" and component != "deployment"
sort location, company asc
```