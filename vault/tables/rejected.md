```dataview
table location, company, tech, component, status, capacity, investment_value, dt_announce
from "src/phases" 
where reject-phase = true and country = "LVA"
sort location, company asc
```

