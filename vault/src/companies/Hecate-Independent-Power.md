```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Hecate-Independent-Power" or company = "Hecate Independent Power")
sort location, dt_announce desc
```
