```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Siemens-Gas-and-Power" or company = "Siemens Gas and Power")
sort location, dt_announce desc
```
