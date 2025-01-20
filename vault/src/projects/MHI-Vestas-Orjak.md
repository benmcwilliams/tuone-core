```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "HRV-09326-02352") and reject-phase = false
sort location, company asc
```
