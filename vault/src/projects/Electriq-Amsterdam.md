```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NLD-00018-04910") and reject-phase = false
sort location, company asc
```
