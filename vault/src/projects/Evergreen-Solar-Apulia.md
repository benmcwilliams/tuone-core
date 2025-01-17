```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ITA-03030-02884") and reject-phase = false
sort location, company asc
```
