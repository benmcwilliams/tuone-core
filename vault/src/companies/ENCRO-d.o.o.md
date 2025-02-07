```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "ENCRO-d.o.o" or company = "ENCRO d.o.o")
sort location, dt_announce desc
```
