import click 
import frappe

@click.command("hospital_hello")
def hospital_hello():
    click.echo("Hello from Hospital Management System!")


# Heavy operation function executed in the background worker
def generate_report(patient_name="John Doe"):
    message = f"Patient report generation started for {patient_name}"
    frappe.logger().info(message)
    print(message)


# Whitelisted API method called by client/browser
@frappe.whitelist()
def generate_patient_report(patient_name="John Doe"):
    frappe.enqueue(
        method="hospital.gptassignment.generate_report",
        queue="short",
        patient_name=patient_name
    )
    return "Patient report generation has been queued"


@frappe.whitelist()
def create_task(task_subject: str) -> str:
    doc = frappe.new_doc("Task")
    doc.subject = task_subject
    doc.insert()
    return doc.name


