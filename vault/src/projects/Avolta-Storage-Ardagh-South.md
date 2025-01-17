```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "IRL-08032-08333") and reject-phase = false
sort location, company asc
```
