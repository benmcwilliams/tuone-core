```dataview
table location, company, tech, component, status, capacity, investment_value, dt_announce
from "src/phases" 
where checked = true and reject-phase = false and country = "LVA"
sort location, company asc
```



