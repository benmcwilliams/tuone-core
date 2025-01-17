```dataview
table location, company, tech, component, status, capacity, investment_value, dt_announce
from "phases" 
where reject-phase = true
sort location, company asc
```