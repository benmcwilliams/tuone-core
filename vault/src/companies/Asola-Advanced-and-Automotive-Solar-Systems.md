```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Asola-Advanced-and-Automotive-Solar-Systems" or company = "Asola Advanced and Automotive Solar Systems")
sort location, dt_announce desc
```
