```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Blauwvinger-Energie" or company = "Blauwvinger Energie")
sort location, dt_announce desc
```
