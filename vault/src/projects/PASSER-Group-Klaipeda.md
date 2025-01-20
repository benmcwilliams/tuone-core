```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "LTU-07389-07971") and reject-phase = false
sort location, company asc
```
