```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Cambridgeshire-County-Council" or company = "Cambridgeshire County Council")
sort location, dt_announce desc
```
