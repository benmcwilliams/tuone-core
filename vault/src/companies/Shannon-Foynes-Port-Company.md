```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Shannon-Foynes-Port-Company" or company = "Shannon Foynes Port Company")
sort location, dt_announce desc
```
