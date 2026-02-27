using UnityEngine;

namespace GestureBodyGame
{
    public class SmoothFollowCamera : MonoBehaviour
    {
        [SerializeField] private Transform target;
        [SerializeField] private Vector3 followOffset = new Vector3(0f, 5f, -8f);
        [SerializeField] private Vector3 lookOffset = new Vector3(0f, 1.2f, 5f);
        [SerializeField] private float positionSmooth = 8f;
        [SerializeField] private float rotationSmooth = 10f;

        private void LateUpdate()
        {
            if (target == null)
            {
                return;
            }

            var desiredPosition = target.position + followOffset;
            transform.position = Vector3.Lerp(
                transform.position,
                desiredPosition,
                1f - Mathf.Exp(-positionSmooth * Time.deltaTime));

            var lookPoint = target.position + lookOffset;
            var desiredRotation = Quaternion.LookRotation(lookPoint - transform.position, Vector3.up);
            transform.rotation = Quaternion.Slerp(
                transform.rotation,
                desiredRotation,
                1f - Mathf.Exp(-rotationSmooth * Time.deltaTime));
        }
    }
}
