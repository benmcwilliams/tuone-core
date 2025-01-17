```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ITA-02660-01978") and reject-phase = false
sort location, company asc
```
