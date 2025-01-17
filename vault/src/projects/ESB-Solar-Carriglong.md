```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "IRL-08489-08694") and reject-phase = false
sort location, company asc
```
