```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Lloyd's-Register" or company = "Lloyd's Register")
sort location, dt_announce desc
```
